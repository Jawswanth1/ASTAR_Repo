from __future__ import annotations

import argparse
import json
import os
import re
import threading
import uuid
import shutil
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .sessions import session_settings
from .converter import convert_pdf, ocr_available
from .storage import (MAX_PACKAGE, atomic_json, install_portable, portable_course,
                      read_course, validate_course, asset_paths)
from . import demo
from . import learn
from .epaper import menu_frame, number_line_frame

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
DATA = ROOT / "data"
LEARNING_ONLY = os.environ.get("ASTAR_LEARNING_ONLY") == "1"
JOBS = {}
LOCK = threading.Lock()
POOL = ThreadPoolExecutor(max_workers=1)
DEMO_JOBS = {}
LEARN_JOBS = {}


def run_learning(book_id, options):
    def progress(done,total,message):
        with LOCK: LEARN_JOBS[book_id].update(done=done,total=total,message=message)
    try:
        learn.build(book_id,options,progress)
        with LOCK: LEARN_JOBS[book_id].update(status='complete',message='Chapter 1 is ready')
    except Exception as exc:
        with LOCK: LEARN_JOBS[book_id].update(status='error',message=str(exc)[:600])


def run_demo(job_id, directory, source, options):
    def progress(done,total,message):
        with LOCK: DEMO_JOBS[job_id].update(done=done,total=total,message=message)
    try:
        with demo.BUILD_LOCK:
            course=demo.build_demo(source,directory,options,progress)
        with LOCK: DEMO_JOBS[job_id].update(status='complete',demoId=course['id'],message='Chapter 1 is ready')
    except Exception as exc:
        with LOCK: DEMO_JOBS[job_id].update(status='error',message=str(exc)[:600])


def run_conversion(job_id, directory, options):
    def progress(done, total, message):
        with LOCK:
            JOBS[job_id].update(done=done, total=total, message=message)
    try:
        course = convert_pdf(directory / "source.pdf", directory, options, progress)
        validate_course(course)
        atomic_json(directory / "course.json", course)
        with LOCK:
            JOBS[job_id].update(status="complete", courseId=course["id"], message="Ready for review")
    except Exception as exc:
        with LOCK:
            JOBS[job_id].update(status="error", message=str(exc)[:600])


def render_reader(course):
    template = (STATIC / "reader.html").read_text(encoding="utf-8")
    content = json.dumps(course, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return template.replace("/*ASTAR_CSS*/", (STATIC / "style.css").read_text(encoding="utf-8") + '\n' + (STATIC / 'quality.css').read_text(encoding='utf-8')).replace(
        "/*ASTAR_BOOK*/", "window.ASTAR_BOOK=" + content + ";").replace(
        "/*ASTAR_READER*/", (STATIC / "reader.js").read_text(encoding="utf-8"))


class Handler(BaseHTTPRequestHandler):
    server_version = "ASTAR/0.2"

    def learning_route(self, method, path):
        if method == "GET":
            return (path in ("/", "/learn", "/learn/", "/learn/index.html",
                             "/learn/app.js", "/learn/style.css") or
                    re.fullmatch(r"/api/learn/(books|jobs)/[a-f0-9]{32}", path) is not None or
                    re.fullmatch(r"/learn/books/[a-f0-9]{32}/.+", path) is not None)
        if method == "POST":
            return (path == "/api/learn/upload" or
                    re.fullmatch(r"/api/learn/build/[a-f0-9]{32}", path) is not None)
        return False

    def log_message(self, format, *args):
        # Keep the console useful during polling.
        if "/api/jobs/" not in str(args[0]):
            super().log_message(format, *args)

    def send(self, body, status=200, content_type="application/json; charset=utf-8", filename=None):
        if not isinstance(body, bytes):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(body)

    def json(self, value, status=200):
        self.send(json.dumps(value, ensure_ascii=False), status)

    def body(self, maximum):
        length = int(self.headers.get("Content-Length", 0))
        if not 0 < length <= maximum:
            raise ValueError(f"Request must be between 1 and {maximum // 1024 // 1024} MB.")
        body = self.rfile.read(length)
        if len(body) != length:
            raise ValueError("Incomplete upload.")
        return body

    def local_request(self):
        host = self.headers.get("Host", "")
        expected = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if self.server.server_address[0] in ("127.0.0.1", "::1"):
            if host not in expected:
                raise ValueError("Use the local ASTAR address.")
        elif not host or any(char in host for char in "\r\n/\\"):
            raise ValueError("A valid Host header is required.")
        origin = self.headers.get("Origin")
        if origin:
            parsed_origin = urlparse(origin)
            if (parsed_origin.scheme not in ("http", "https") or
                    parsed_origin.netloc.casefold() != host.casefold()):
                raise ValueError("Cross-origin requests are not allowed.")

    def do_GET(self):
        try:
            self.local_request()
            path = urlparse(self.path).path
            if LEARNING_ONLY and not self.learning_route("GET", path):
                return self.json({"error": "Not found"}, 404)
            match=re.fullmatch(r'/api/learn/(books|jobs)/([a-f0-9]{32})',path)
            if match:
                if match[1]=='books':return self.json(learn.get(match[2]))
                with LOCK: job=dict(LEARN_JOBS.get(match[2],dict(status='error',message='Preparation was interrupted. Upload the textbook again.')))
                return self.json(job)
            match=re.fullmatch(r'/learn/books/([a-f0-9]{32})/(.+)',path)
            if match:
                file=learn.asset(match[1],match[2]);return self.send(file.read_bytes(),content_type='application/pdf' if file.suffix=='.pdf' else 'image/png')
            if path in ('/','/learn','/learn/') or path.startswith('/learn/'):
                relative='index.html' if path in ('/','/learn','/learn/') else path[len('/learn/'):]
                if relative not in ('index.html','app.js','style.css'):return self.json({'error':'Not found'},404)
                file=STATIC/'learn'/relative
                return self.send(file.read_bytes(),content_type={'.html':'text/html','.js':'text/javascript','.css':'text/css'}[file.suffix]+'; charset=utf-8')
            if path == '/api/demos':
                return self.json(demo.list_demos())
            if path == '/api/demo-numberline':
                query=parse_qs(urlparse(self.path).query)
                return self.send(number_line_frame(int(query.get('n',['0'])[0])).png(),content_type='image/png')
            match=re.fullmatch(r'/api/demo-jobs/([a-f0-9]{32})',path)
            if match:
                with LOCK: job=dict(DEMO_JOBS.get(match[1],dict(status='error',message='Job not found.')))
                return self.json(job)
            match=re.fullmatch(r'/api/demos/([a-f0-9]{32})(?:/(export))?',path)
            if match:
                if match[2]:
                    return self.send(demo.export_demo(match[1]).read_bytes(),content_type='application/zip',filename='astar-chapter-one.zip')
                return self.json(demo.get_demo(match[1]))
            match=re.fullmatch(r'/demos/([a-f0-9]{32})/(.+)',path)
            if match:
                file=demo.demo_asset(match[1],match[2])
                mime={'.png':'image/png','.bin':'application/octet-stream','.pdf':'application/pdf','.txt':'text/plain; charset=utf-8','.json':'application/json'}[file.suffix]
                return self.send(file.read_bytes(),content_type=mime)
            if path in ('/demo','/demo/') or path.startswith('/demo/'):
                relative='index.html' if path in ('/demo','/demo/') else path[len('/demo/'):]
                if relative not in ('index.html','app.js','style.css'):return self.json({'error':'Not found'},404)
                file=STATIC/'demo'/relative
                mime={'.html':'text/html','.js':'text/javascript','.css':'text/css'}[file.suffix]
                return self.send(file.read_bytes(),content_type=mime+'; charset=utf-8')
            if path == "/api/status":
                return self.json({"ocr": ocr_available(), "version": "0.2.0", "dataPath": str(DATA)})
            if path == "/api/courses":
                courses = []
                for file in sorted(DATA.glob("*/course.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                    course = read_course(file.parent)
                    courses.append({"id": course["id"], "title": course["title"], "subject": course["subject"],
                                    "chapters": len(course["chapters"]), "lessons": len(course["lessons"]),
                                    "reviewed": sum(l["reviewed"] for l in course["lessons"]),
                                    "attention": course['report']['quality']['attention'],
                                    "automatic": course['report']['quality']['automatic'],
                                    "analyzerVersion": course['report'].get('analysis',{}).get('version','1.0')})
                return self.json(courses)
            match = re.fullmatch(r"/api/jobs/([a-f0-9]{32})", path)
            if match:
                with LOCK:
                    job = dict(JOBS.get(match[1], {"status": "error", "message": "Job not found. Re-open the library to check completed imports."}))
                return self.json(job)
            match = re.fullmatch(r"/api/courses/([a-f0-9]{32})(?:/(export|reader))?", path)
            if match:
                directory = DATA / match[1]
                if match[2] == "export":
                    return self.send(json.dumps(portable_course(directory), ensure_ascii=False), filename="course.astar.json")
                if match[2] == "reader":
                    return self.send(render_reader(portable_course(directory)), content_type="text/html; charset=utf-8", filename="astar-reader.html")
                return self.json(read_course(directory))
            match = re.fullmatch(r"/courses/([a-f0-9]{32})/(assets/(?:(?:original|page)-\d{4,5}|figure-\d{4,5}-\d{2}|focus-\d{5}-\d{4})\.png|source\.pdf)", path)
            if match:
                file = DATA / match[1] / match[2]
                return self.send(file.read_bytes(), content_type="application/pdf" if file.suffix == ".pdf" else "image/png")
            mapping = {"/": "index.html", "/app.js": "app.js", "/reader.js": "reader.js", "/style.css": "style.css", '/quality.css':'quality.css', '/brand.css':'brand.css', '/logo.png':'logo.png'}
            if path in mapping:
                file = STATIC / mapping[path]
                mime = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".png": "image/png"}[file.suffix]
                return self.send(file.read_bytes(), content_type=mime if file.suffix == '.png' else mime + "; charset=utf-8")
            if path == '/structure.js':
                return self.send((STATIC/'structure.js').read_bytes(),content_type='text/javascript; charset=utf-8')
            if path in ('/product', '/product/') or path.startswith('/product/'):
                relative = 'index.html' if path in ('/product', '/product/') else path[len('/product/'):]
                directory = (STATIC / 'product').resolve()
                file = (directory / relative).resolve()
                if not file.is_relative_to(directory) or not file.is_file():
                    return self.json({'error': 'Not found'}, 404)
                mime = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
                        '.json': 'application/json', '.md': 'text/plain'}.get(file.suffix, 'application/octet-stream')
                return self.send(file.read_bytes(), content_type=mime)
            self.json({"error": "Not found"}, 404)
        except FileNotFoundError:
            self.json({"error": "Course or file not found."}, 404)
        except (ValueError, TypeError, KeyError) as exc:
            self.json({"error": str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        try:
            self.local_request()
            parsed = urlparse(self.path)
            if LEARNING_ONLY and not self.learning_route("POST", parsed.path):
                return self.json({"error": "Not found"}, 404)
            if parsed.path=='/api/learn/upload':
                query={k:v[0] for k,v in parse_qs(parsed.query).items()}
                body=self.body(100*1024*1024)
                if b'%PDF-' not in body[:1024]:raise ValueError('Choose a valid textbook PDF.')
                book_id=uuid.uuid4().hex;directory=learn.directory(book_id);directory.mkdir(parents=True)
                (directory/'source.pdf').write_bytes(body)
                return self.json(learn.inspect(book_id,query.get('filename','Textbook.pdf')),201)
            match=re.fullmatch(r'/api/learn/build/([a-f0-9]{32})',parsed.path)
            if match:
                options=json.loads(self.body(8192));book_id=match[1]
                if not (learn.directory(book_id)/'upload.json').exists():raise ValueError('Upload a textbook first.')
                with LOCK:
                    if LEARN_JOBS.get(book_id,{}).get('status')=='working':return self.json({'id':book_id},202)
                    LEARN_JOBS[book_id]=dict(status='working',done=0,total=1,message='Preparing Chapter 1')
                POOL.submit(run_learning,book_id,options)
                return self.json({'id':book_id},202)
            if parsed.path == '/api/demo-menu':
                data=json.loads(self.body(32*1024))
                entries=data.get('entries',[])
                if not isinstance(entries,list) or not 1<=len(entries)<=120 or any(not isinstance(e,str) or len(e)>60 for e in entries):
                    raise ValueError('Invalid menu entries.')
                return self.send(menu_frame(str(data.get('title','ASTAR'))[:45],entries,
                    int(data.get('selected',0)),str(data.get('subtitle','ASTAR / Chapter 1'))[:65]).png(),content_type='image/png')
            if parsed.path in ('/api/demo-import','/api/demo-scert'):
                with LOCK:
                    if any(j['status']=='working' for j in DEMO_JOBS.values()):
                        return self.json({'error':'Wait for the current demonstration import.'},409)
                query={k:v[0] for k,v in parse_qs(parsed.query).items()}
                directory=demo.DEMO_DATA/uuid.uuid4().hex
                if parsed.path=='/api/demo-scert':
                    existing=next((c for c in demo.list_demos() if demo.get_demo(c['id'])['source']['sha256']==demo.SCERT_HASH and demo.get_demo(c['id']).get('version')==demo.VERSION),None)
                    if existing:return self.json({'demoId':existing['id']})
                    source=ROOT/'8 maths em 2020-21.pdf'
                    if not source.is_file():raise ValueError('The local SCERT reference PDF was not found.')
                else:
                    body=self.body(100*1024*1024)
                    if b'%PDF-' not in body[:1024]:raise ValueError('Choose a valid PDF.')
                    directory.mkdir(parents=True)
                    source=directory/'source.pdf';source.write_bytes(body)
                job_id=uuid.uuid4().hex
                with LOCK: DEMO_JOBS[job_id]=dict(status='working',done=0,total=1,message='Opening chapter-one source')
                POOL.submit(run_demo,job_id,directory,source,query)
                return self.json({'jobId':job_id},202)
            rebuild = re.fullmatch(r'/api/courses/([a-f0-9]{32})/rebuild', parsed.path)
            if rebuild:
                old = DATA / rebuild[1]
                if not (old / 'source.pdf').exists():
                    raise ValueError('This transferred course has no source PDF. Import the original PDF to rebuild it.')
                with LOCK:
                    if any(j['status']=='working' for j in JOBS.values()):
                        return self.json({'error':'Wait for the current import to finish.'},409)
                original = read_course(old)
                new_id, job_id = uuid.uuid4().hex, uuid.uuid4().hex
                directory = DATA / new_id
                directory.mkdir()
                shutil.copyfile(old/'source.pdf', directory/'source.pdf')
                options = {**original.get('settings',{}), 'title':original['title'], 'subject':original['subject'],
                           'language':original['language'], 'filename':original['source']['filename']}
                with LOCK:
                    JOBS[job_id] = {'status':'working','done':0,'total':1,'message':'Rebuilding with document analysis'}
                POOL.submit(run_conversion,job_id,directory,options)
                return self.json({'jobId':job_id},202)
            if parsed.path == "/api/import":
                with LOCK:
                    if any(j["status"] == "working" for j in JOBS.values()):
                        return self.json({"error": "A textbook is already being prepared. Wait for it to finish."}, 409)
                query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                timing = session_settings(query)
                query.update(timing)
                word_limit, minimum = int(query.get("wordsPerLesson", 220)), int(query.get("minLessons", 150))
                if timing["planningMode"] == "words" and (not 80 <= word_limit <= 1200 or not 1 <= minimum <= 2000):
                    raise ValueError("Use 80-1,200 words per lesson and a target of 1-2,000 lessons.")
                if len(query.get("chapterPlan", "")) > 100000 or len(query.get("title", "")) > 500:
                    raise ValueError("Import settings are too long.")
                body = self.body(200 * 1024 * 1024)
                if b"%PDF-" not in body[:1024]:
                    raise ValueError("Select a valid PDF file.")
                course_id, job_id = uuid.uuid4().hex, uuid.uuid4().hex
                directory = DATA / course_id
                directory.mkdir()
                (directory / "source.pdf").write_bytes(body)
                query.update(wordsPerLesson=word_limit, minLessons=minimum, ocr=query.get("ocr", "true") == "true")
                with LOCK:
                    JOBS[job_id] = {"status": "working", "done": 0, "total": 1, "message": "Opening PDF"}
                POOL.submit(run_conversion, job_id, directory, query)
                return self.json({"jobId": job_id}, 202)
            if parsed.path == "/api/packages":
                course = json.loads(self.body(MAX_PACKAGE))
                installed = install_portable(course, DATA)
                return self.json({"courseId": installed["id"]}, 201)
            self.json({"error": "Not found"}, 404)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            self.json({"error": str(exc)[:600]}, 400)

    def do_PUT(self):
        try:
            self.local_request()
            if LEARNING_ONLY:
                return self.json({"error": "Not found"}, 404)
            match = re.fullmatch(r"/api/courses/([a-f0-9]{32})", self.path)
            if not match:
                return self.json({"error": "Not found"}, 404)
            directory = DATA / match[1]
            existing = read_course(directory)
            course = validate_course(json.loads(self.body(30 * 1024 * 1024)))
            if course["id"] != existing["id"]:
                raise ValueError("Course ID cannot be changed.")
            if existing.get('structure') and course.get('structure',{}).get('evidenceHash') != existing['structure']['evidenceHash']:
                raise ValueError('Original extraction evidence cannot be changed. Record a correction separately.')
            for asset in asset_paths(course):
                if not (directory / asset).is_file():
                    raise ValueError("A referenced source image is missing.")
            atomic_json(directory / "course.json", course)
            self.json({"saved": True, 'quality':course['report']['quality'],
                       'lessonQuality':[{'id':l['id'],'quality':l['quality'],'warnings':l['warnings']} for l in course['lessons']]})
        except FileNotFoundError:
            self.json({"error": "Course not found"}, 404)
        except (ValueError, TypeError, KeyError) as exc:
            self.json({"error": str(exc)[:600]}, 400)


def main():
    global DATA
    parser = argparse.ArgumentParser(description="ASTAR textbook learning app")
    parser.add_argument("--host", default=os.environ.get("ASTAR_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("ASTAR_DATA_DIR", DATA)))
    args = parser.parse_args()
    DATA = args.data_dir.resolve()
    DATA.mkdir(parents=True, exist_ok=True)
    learn.DATA = DATA / "learning-data"
    demo.DEMO_DATA = DATA / "demo-data"
    learn.DATA.mkdir(parents=True, exist_ok=True)
    if not LEARNING_ONLY:
        demo.DEMO_DATA.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"ASTAR is listening on {args.host}:{server.server_port}", flush=True)
    print(f"ASTAR data directory: {DATA}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
