from __future__ import annotations

import base64
import json
import re
import uuid
from pathlib import Path

from PIL import Image
import io

SCHEMA = "astar-1"
ID = re.compile(r"[a-zA-Z0-9_-]{1,80}\Z")
ASSET = re.compile(r"assets/(?:(?:original|page)-\d{4,5}|figure-\d{4,5}-\d{2}|focus-\d{5}-\d{4})\.png\Z")
MAX_PACKAGE = 300 * 1024 * 1024


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(".tmp-" + uuid.uuid4().hex)
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def text(value, name, limit=100000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f"Invalid {name}.")


def validate_course(course):
    if not isinstance(course, dict) or course.get("schemaVersion") != SCHEMA:
        raise ValueError("Expected an ASTAR course package (astar-1).")
    if not isinstance(course.get("id"), str) or not ID.fullmatch(course["id"]):
        raise ValueError("Invalid course ID.")
    for key in ("title", "subject", "language"):
        text(course.get(key), key, 500)
    source = course.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("pages"), int) or not 1 <= source["pages"] <= 2000:
        raise ValueError("Invalid source page count.")
    text(source.get("filename"), "source filename", 1000)
    if not isinstance(source.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", source["sha256"]):
        raise ValueError("Invalid source checksum.")
    def page_number(value):
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= source["pages"]:
            raise ValueError("Invalid PDF page reference.")
    def warnings(value):
        if not isinstance(value, list) or len(value) > 10000:
            raise ValueError("Invalid warning list.")
        for warning in value:
            text(warning, "warning", 2000)
    report = course.get("report")
    if not isinstance(report, dict) or not isinstance(report.get("words"), int) or report["words"] < 0:
        raise ValueError("Invalid conversion report.")
    text(report.get("chapterMethod"), "chapter method", 1000)
    warnings(report.get("warnings"))
    if not isinstance(report.get("pages"), list) or len(report["pages"]) != source["pages"]:
        raise ValueError("Invalid page report.")
    for row in report["pages"]:
        if not isinstance(row, dict):
            raise ValueError("Invalid page report entry.")
        page_number(row.get("number"))
        text(row.get("source"), "extraction source", 100)
        if not isinstance(row.get("image"), str) or not ASSET.fullmatch(row["image"]):
            raise ValueError("Invalid report image path.")
        warnings(row.get("warnings"))
        if 'issues' in row:
            if not isinstance(row['issues'],list) or len(row['issues'])>1000:
                raise ValueError('Invalid page issues.')
            for diagnostic in row['issues']:
                if not isinstance(diagnostic,dict) or diagnostic.get('severity') not in ('high','medium','low'):
                    raise ValueError('Invalid issue severity.')
                text(diagnostic.get('message'),'issue message',2000)
                text(diagnostic.get('code'),'issue code',100)
                if not isinstance(diagnostic.get('pages'),list) or len(diagnostic['pages'])>2000:
                    raise ValueError('Invalid issue page list.')
                for number in diagnostic['pages']:page_number(number)
        if row.get('disposition') is not None and row['disposition'] not in ('learning','excluded'):
            raise ValueError('Invalid page disposition.')
    chapters, lessons = course.get("chapters"), course.get("lessons")
    if not isinstance(chapters, list) or not 1 <= len(chapters) <= 2000:
        raise ValueError("Course needs chapters.")
    if not isinstance(lessons, list) or not 1 <= len(lessons) <= 20000:
        raise ValueError("Course needs 1 to 20,000 lessons.")
    ids = set()

    def register(obj):
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not ID.fullmatch(obj["id"]) or obj["id"] in ids:
            raise ValueError("Missing, invalid or duplicate content ID.")
        ids.add(obj["id"])

    for chapter in chapters:
        register(chapter)
        text(chapter.get("title"), "chapter title", 500)
        page_number(chapter.get("startPage"))
    chapter_ids = {c["id"] for c in chapters}
    for lesson in lessons:
        register(lesson)
        text(lesson.get("title"), "lesson title", 500)
        if lesson.get("chapterId") not in chapter_ids:
            raise ValueError("Lesson refers to an unknown chapter.")
        if not isinstance(lesson.get("reviewed"), bool):
            raise ValueError("Invalid review state.")
        page_number(lesson.get("pageStart"))
        page_number(lesson.get("pageEnd"))
        warnings(lesson.get("warnings"))
        if not isinstance(lesson.get("blocks"), list) or len(lesson["blocks"]) > 10000:
            raise ValueError("Invalid lesson blocks.")
        for block in lesson["blocks"]:
            register(block)
            if block.get("type") not in ("text", "question", "source", "figure"):
                raise ValueError("Unsupported block type.")
            text(block.get("text"), "block text")
            page_number(block.get("page"))
            text(block.get("source"), "block source", 100)
            if block['type'] == 'figure' and (not isinstance(block.get('image'), str) or not ASSET.fullmatch(block['image'])):
                raise ValueError('Invalid figure image path.')
        if not isinstance(lesson.get("panels"), list) or len(lesson["panels"]) > 2000:
            raise ValueError("Invalid source panels.")
        for panel in lesson["panels"]:
            if not isinstance(panel, dict) or not isinstance(panel.get("image"), str) or not ASSET.fullmatch(panel["image"]):
                raise ValueError("Invalid source image path.")
            page_number(panel.get("page"))
            if panel.get('focusImage') is not None and (not isinstance(panel['focusImage'],str) or not ASSET.fullmatch(panel['focusImage'])):
                raise ValueError('Invalid focused lesson image.')
        if not isinstance(lesson.get("questions"), list) or len(lesson["questions"]) > 1000:
            raise ValueError("Invalid lesson questions.")
        block_ids = {b["id"] for b in lesson["blocks"]}
        for question in lesson["questions"]:
            register(question)
            text(question.get("prompt"), "question prompt", 20000)
            if not question["prompt"].strip():
                raise ValueError("Enter a prompt for every practice question before saving.")
            if question.get("type") not in ("mcq", "notebook") or question.get("placement") not in ("middle", "end"):
                raise ValueError("Invalid question type or placement.")
            if question.get("afterBlockId") and question["afterBlockId"] not in block_ids:
                raise ValueError("Question placement refers to a missing text block.")
            if question["type"] == "mcq":
                options = question.get("options")
                if not isinstance(options, list) or not 2 <= len(options) <= 6:
                    raise ValueError("MCQs need 2 to 6 options.")
                for option in options:
                    text(option, "answer option", 2000)
                    if not option.strip():
                        raise ValueError("Fill every MCQ option before saving.")
                answer = question.get("answer")
                if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < len(options):
                    raise ValueError("MCQ needs a valid answer index.")
    analysis = report.get('analysis')
    if analysis is not None:
        if not isinstance(analysis, dict) or not isinstance(analysis.get('excluded'), list) or len(analysis['excluded']) > 200000:
            raise ValueError('Invalid exclusion log.')
        for entry in analysis['excluded']:
            if not isinstance(entry, dict):
                raise ValueError('Invalid exclusion entry.')
            for key in ('id','text','reason','category'):
                text(entry.get(key), 'exclusion '+key)
            page_number(entry.get('page'))
            if not isinstance(entry.get('restored'),bool):
                raise ValueError('Invalid exclusion restore state.')
    if 'structure' in course:
        from .structure import validate_structure
        validate_structure(course['structure'],source['pages'],chapter_ids)
    # Recompute risk from source evidence; never trust a supplied "all clear" flag.
    from .analysis import assess_course
    return assess_course(course)


def read_course(directory):
    return validate_course(json.loads((Path(directory) / "course.json").read_text(encoding="utf-8")))


def portable_course(directory):
    directory = Path(directory)
    course = read_course(directory)
    paths = asset_paths(course)
    course["assets"] = {p: "data:image/png;base64," + base64.b64encode((directory / p).read_bytes()).decode("ascii") for p in paths}
    return course


def install_portable(course, root):
    validate_course(course)
    assets = course.pop("assets", None)
    if not isinstance(assets, dict):
        raise ValueError("Package is missing embedded images.")
    paths = asset_paths(course)
    if len(paths) > 62000:
        raise ValueError("Too many page images.")
    course["id"] = uuid.uuid4().hex
    directory = Path(root) / course["id"]
    directory.mkdir()
    try:
        (directory / "assets").mkdir()
        for path in paths:
            value = assets.get(path, "")
            if not isinstance(value, str) or not value.startswith("data:image/png;base64,") or len(value) > 12_000_000:
                raise ValueError("Invalid or oversized image in package.")
            image_bytes = base64.b64decode(value.split(",", 1)[1], validate=True)
            with Image.open(io.BytesIO(image_bytes)) as image:
                if image.format != "PNG" or image.width * image.height > 10_000_000:
                    raise ValueError("Expected a bounded PNG page image.")
                image.verify()
            (directory / path).write_bytes(image_bytes)
        atomic_json(directory / "course.json", course)
    except Exception:
        import shutil
        shutil.rmtree(directory)
        raise
    return course


def asset_paths(course):
    return ({p['image'] for p in course.get('structure',{}).get('evidence',{}).get('pages',[])}
            | {p['image'] for l in course['lessons'] for p in l['panels']}
            | {p['focusImage'] for l in course['lessons'] for p in l['panels'] if p.get('focusImage')}
            | {p['image'] for p in course['report']['pages']}
            | {b['image'] for l in course['lessons'] for b in l['blocks'] if b['type']=='figure'})
