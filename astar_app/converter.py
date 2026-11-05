"""PDF extraction with source images, provenance and explicit review warnings.

Never paraphrases, creates answers or silently substitutes generated content.
"""
from __future__ import annotations

import hashlib
import copy
import io
import math
import os
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pymupdf as pdf
from PIL import Image, ImageOps
from .sessions import session_settings, plan_sessions
from .structure import reconstruct
from .analysis import analyze_pages, assess_course, looks_like_question, FRONT, BACK, CHAPTER


def tesseract_path():
    candidates = [os.environ.get("ASTAR_TESSERACT"), shutil.which("tesseract"),
                  r"C:\Program Files\Tesseract-OCR\tesseract.exe"]
    return next((p for p in candidates if p and Path(p).is_file()), None)


def ocr_available():
    try:
        import pytesseract  # noqa: F401
        return bool(tesseract_path())
    except ImportError:
        return False


def count_words(text):
    # Counts scripts without spaces conservatively as well as whitespace words.
    return len(re.findall(r"\S+", text))


def split_text(text, limit):
    """Prefer sentence endings; never delete or rewrite any characters."""
    result = []
    remaining = text
    while True:
        tokens = list(re.finditer(r"\S+", remaining))
        if len(tokens) <= limit:
            result.append(remaining)
            return result
        ceiling = tokens[limit].start()
        floor = tokens[max(0, int(limit*.5))].start()
        boundaries = [m.end() for m in re.finditer(r'[.!?][\"\u201d\u2019)]*\s+', remaining[:ceiling]) if m.end() >= floor]
        cut = boundaries[-1] if boundaries else ceiling
        result.append(remaining[:cut])
        remaining = remaining[cut:]


def chapter_plan(doc, manual, pages):
    learning = {p['number'] for p in pages if p['disposition'] == 'learning'}
    if manual:
        entries = []
        for row in manual.splitlines():
            if not row.strip():
                continue
            match = re.fullmatch(r"\s*(\d+)\s*\|\s*(.+?)\s*", row)
            if not match:
                raise ValueError("Chapter lines must use: PDF page number | Chapter title")
            entries.append((int(match[1]), match[2]))
        if not entries:
            raise ValueError("Enter at least one chapter.")
        if len({p for p, _ in entries}) != len(entries):
            raise ValueError("Each chapter needs a different start page.")
        method = "manual"
    else:
        toc = [e for e in doc.get_toc() if e[2] in learning and not FRONT.fullmatch(e[1].strip()) and not BACK.fullmatch(e[1].strip())]
        if toc:
            level = min(e[0] for e in toc)
            entries = [(e[2], e[1]) for e in toc if e[0] == level]
            method = "PDF bookmarks checked against learning pages"
        else:
            entries = []
            seen = set()
            for page in pages:
                if page['number'] not in learning:
                    continue
                for block in page['blocks'][:8]:
                    line = block['text'].splitlines()[0].strip()
                    if CHAPTER.match(line) and block.get('role') == 'heading':
                        key = re.match(r'^(?:chapter|unit)\s+(\w+)', line, re.I)[0].casefold()
                        if key not in seen:
                            entries.append((page['number'], line[:200])); seen.add(key)
                        break
            method = "chapter headings and document layout"
        if not entries:
            entries = [(min(learning), "Textbook")]
            method = "single chapter (no explicit chapter markers found)"
    entries = sorted(dict(entries).items())
    if not manual:
        by_page = dict(entries)
        for page in pages:
            if page['number'] not in learning:
                continue
            candidates = [b for b in page['blocks'] if b.get('role')=='heading' and b.get('size',0)>=17
                          and b['bbox'][1]<page['height']*.30 and not re.fullmatch(r'\s*(?:chapter\s*\d*|\d+\s*chapter|\d+)\s*',b['text'],re.I)]
            if (page.get('chapterMarker') or page['number'] in by_page) and candidates:
                best = max(b['size'] for b in candidates)
                title = ' '.join(' '.join(b['text'].split()) for b in sorted(candidates,key=lambda b:b['bbox'][1]) if b['size']>=best*.88)
                by_page[page['number']] = title[:200]
        entries = sorted(by_page.items())
    if any(p < 1 or p > len(doc) for p, _ in entries):
        raise ValueError(f"Chapter start pages must be between 1 and {len(doc)}.")
    if not manual and min(learning) < entries[0][0]:
        # Preserve a substantive learning introduction, not cover/publication pages.
        entries.insert(0, (min(learning), "Introduction"))
    return [{"id": f"ch-{i+1}", "title": title, "startPage": page}
            for i, (page, title) in enumerate(entries)], method


def extract_ocr(page, language):
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = tesseract_path()
    pix = page.get_pixmap(dpi=180, colorspace=pdf.csGRAY, alpha=False)
    image = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    data = pytesseract.image_to_data(image, lang=language, timeout=90,
                                    output_type=pytesseract.Output.DICT)
    groups = {}
    confidence = []
    sx, sy = page.rect.width / pix.width, page.rect.height / pix.height
    for i, text in enumerate(data["text"]):
        if not text.strip():
            continue
        key = (data["block_num"][i], data["par_num"][i])
        x, y, w, h = (data[k][i] for k in ("left", "top", "width", "height"))
        group = groups.setdefault(key, {"text": [], "bbox": [x*sx, y*sy, (x+w)*sx, (y+h)*sy]})
        group["text"].append(text)
        b = group["bbox"]
        b[:] = [min(b[0], x*sx), min(b[1], y*sy), max(b[2], (x+w)*sx), max(b[3], (y+h)*sy)]
        confidence.append(float(data["conf"][i]))
    return [{"text": " ".join(g["text"]), "bbox": g["bbox"], "size": 0}
            for g in groups.values()], round(sum(confidence)/max(1, len(confidence)), 1)


def learning_pixmap(page, scale, native=None):
    """Hide isolated rotated text stamps for rendering, then restore the PDF in memory.

    Only a tiny text-only Form XObject matching a large diagonal text span is
    eligible. No rectangle redaction is used: overlapping teaching text survives.
    Unknown encodings and mixed graphics forms are left untouched.
    """
    native = native or page.get_text('dict',flags=pdf.TEXTFLAGS_DICT & ~pdf.TEXT_PRESERVE_IMAGES)
    stamps = set()
    for block in native['blocks']:
        for line in block.get('lines',[]):
            value = ''.join(s['text'] for s in line['spans'])
            if abs(line.get('dir',(1,0))[1])>.3 and any(s['size']>35 for s in line['spans']) and 4<=len(value.strip())<=100:
                stamps.add(' '.join(value.split()))
    saved = {}
    doc = page.parent
    try:
        if stamps:
            for xref, *_ in page.get_xobjects():
                data = doc.xref_stream(xref)
                if not data or len(data)>8192 or re.search(rb'\b(?:Do|BI|m|l|re|S|f)\b',data):
                    continue
                literals = re.findall(rb'\(([^()\\]*)\)\s*Tj\b',data)
                if len(literals)==1 and data.count(b'BT')==1:
                    value=' '.join(literals[0].decode('latin1').split())
                    if value in stamps:
                        saved[xref]=data;doc.update_stream(xref,b'')
        return page.get_pixmap(matrix=pdf.Matrix(scale,scale),colorspace=pdf.csGRAY,alpha=False),bool(saved)
    finally:
        for xref,data in saved.items():doc.update_stream(xref,data)


def extract_page(page, number, asset_dir, use_ocr, language, mode):
    warnings = []
    if page.rotation:
        page.remove_rotation()
    if page.rect.width * page.rect.height > 10_000_000:
        raise ValueError(f"Page {number} is too large to render safely.")
    # Render at a bounded resolution. Bilevel PNG is compact and works on a 1-bit display.
    scale = min(1.6, 1400 / max(page.rect.width, page.rect.height))
    # Genuine source rendering: no stamp removal, cropping or thresholding.
    original_asset = f"original-{number:04d}.png"
    page.get_pixmap(matrix=pdf.Matrix(scale,scale), colorspace=pdf.csGRAY, alpha=False).save(asset_dir/original_asset)
    native = page.get_text('dict', flags=pdf.TEXTFLAGS_DICT & ~pdf.TEXT_PRESERVE_IMAGES)
    pix, removed_stamp = learning_pixmap(page,scale,native)
    image = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    image = ImageOps.autocontrast(image)
    # Large, pale, diagonal publisher watermarks would become distracting dotted
    # text after dithering. Threshold those pages while preserving their black ink.
    pale_watermark = any(abs(line.get('dir',(1,0))[1])>.3 and any(s['size']>35 for s in line['spans']) for b in native['blocks'] for line in b.get('lines',[]))
    if mode == "threshold" or (pale_watermark and not removed_stamp):
        cutoff = 140 if pale_watermark and not removed_stamp else 180
        image = image.point(lambda p: 255 if p > cutoff else 0).convert("1")
    else:
        image = image.convert("1")  # Floyd-Steinberg preserves colour/shading as patterns.
    asset = f"page-{number:04d}.png"
    image.save(asset_dir / asset, optimize=True)
    has_ink = image.getextrema()[0] == 0

    # Vector drawings and embedded illustrations become monochrome figure crops.
    visuals = []
    for info in page.get_image_info():
        r = pdf.Rect(info['bbox'])
        if 80 < r.get_area() < page.rect.get_area()*.75:
            visuals.append(list(r))
    math_blocks = 0
    for block in native['blocks']:
        lines = block.get('lines',[])
        fonts = ' '.join(s.get('font','') for l in lines for s in l['spans'])
        tokens = [''.join(s['text'] for s in l['spans']).strip() for l in lines]
        if re.search(r'symbol|mtextra|cmsy|cmex|math',fonts,re.I) or sum(bool(re.fullmatch(r'[\d+\-−=(),.a-zA-Z]',t)) for t in tokens)>=4:
            math_blocks += 1
    for drawing in ([] if math_blocks>=2 else page.get_drawings()[:2000]):
        r = drawing['rect']
        if max(r.width, r.height) > 15 and r.get_area() < page.rect.get_area()*.65:
            visuals.append(list(r))
    merged = []
    for raw_rect in visuals:
        r = pdf.Rect(raw_rect)
        close = [i for i, old in enumerate(merged) if (pdf.Rect(old) + (-14,-14,14,14)).intersects(r)]
        for i in reversed(close):
            r |= pdf.Rect(merged.pop(i))
        merged.append(list(r))

    raw = page.get_text("dict", flags=pdf.TEXTFLAGS_DICT & ~pdf.TEXT_PRESERVE_IMAGES, sort=True)
    blocks = []
    for block in raw["blocks"]:
        if block.get("type") != 0:
            continue
        lines = block.get("lines", [])
        text = "\n".join("".join(s["text"] for s in line["spans"]) for line in lines)
        if text.strip():
            sizes = [s["size"] for line in lines for s in line["spans"]]
            fonts = ' '.join(s.get('font','') for line in lines for s in line['spans'])
            tiny_lines = sum(bool(re.fullmatch(r'\s*[\d+\-−=(),.a-zA-Z]\s*',line)) for line in text.splitlines())
            math_layout = bool(re.search(r'symbol|mtextra|cmsy|cmex|math',fonts,re.I)) or tiny_lines>=4
            blocks.append({"text": text, "bbox": list(block["bbox"]), "size": max(sizes, default=0), 'mathLayout':math_layout,
                           'lines':[{'text':''.join(s['text'] for s in line['spans']), 'bbox':list(line['bbox'])} for line in lines]})
    source = "text"
    confidence = None
    if len("".join(b["text"] for b in blocks).strip()) < 30:
        if use_ocr and ocr_available():
            try:
                blocks, confidence = extract_ocr(page, language)
                source = "ocr"
                warnings.append("OCR text needs checking against the source image.")
                if confidence is not None and confidence < 75:
                    warnings.append(f"Low OCR confidence ({confidence}%).")
            except Exception as exc:
                warnings.append(f"OCR failed: {str(exc)[:180]}. Source image retained.")
        else:
            warnings.append("Little or no extractable text. Source image retained; install Tesseract for OCR or transcribe in Review.")
    text = "\n".join(b["text"] for b in blocks)
    if "\ufffd" in text:
        warnings.append("Some characters could not be decoded; compare the source image.")
    structure_visuals=[]
    for drawing in page.get_drawings()[:2000]:
        r=drawing['rect']
        if max(r.width,r.height)>20 and r.y0>page.rect.height*.14 and r.y1<page.rect.height*.90 and r.get_area()<page.rect.get_area()*.5:
            structure_visuals.append(list(r))
    structure_visuals.extend(merged)
    tables=[]
    try:
        # Ruled tables only. Borderless grids remain source-layout evidence.
        for table in page.find_tables().tables[:30]:
            tables.append({'bbox':list(table.bbox),'cells':table.extract()})
    except Exception as exc:
        warnings.append('Table detection incomplete: '+str(exc)[:100])
    return {"number": number, "width": page.rect.width, "height": page.rect.height,
            "originalImage":f"assets/{original_asset}", 'structureVisuals':structure_visuals, 'tables':tables,
            "image": f"assets/{asset}", "blocks": blocks, "source": source,
            "ocrConfidence": confidence, "warnings": warnings, "visuals": merged,
            "hasInk": has_ink, 'stampRemovedFromRender':removed_stamp}


def is_question(text):
    return looks_like_question(text)


def convert_pdf(source, output, options, progress=lambda *_: None):
    timing = session_settings(options)
    output, source = Path(output), Path(source)
    output.mkdir(parents=True, exist_ok=True)
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    with pdf.open(source) as doc:
        if doc.needs_pass:
            raise ValueError("This PDF requires a password. Import an unlocked copy.")
        if not 1 <= len(doc) <= 2000:
            raise ValueError("A textbook must contain 1 to 2,000 pages.")
        pages = []
        for i, page in enumerate(doc):
            progress(i, len(doc), f"Extracting page {i+1} of {len(doc)}")
            pages.append(extract_page(page, i+1, assets, options.get("ocr", True),
                                      options.get("language", "eng"), options.get("imageMode", "dither")))
        progress(len(doc), len(doc), "Separating learning content from page furniture")
        raw_pages = copy.deepcopy(pages)
        analysis = analyze_pages(pages, doc.get_toc())
        if not any(p['disposition'] == 'learning' for p in pages):
            raise ValueError("No learning pages found. This PDF appears to contain only front matter or reference pages.")
        chapters, method = chapter_plan(doc, options.get("chapterPlan", ""), pages)
        if options.get('chapterPlan'):
            for page in pages[:chapters[0]['startPage']-1]:
                if page['disposition'] == 'learning':
                    page.update(disposition='excluded', excludedReason='Before the first chapter in your chapter plan')
                    for block in page['blocks']:
                        analysis['excluded'].append({'id':'excluded-'+block['id'], 'page':page['number'], 'text':block['text'],
                            'bbox':block['bbox'], 'reason':page['excludedReason'], 'category':'page', 'restored':False})
                    page['blocks'] = []

    total_words = sum(count_words(b["text"]) for p in pages for b in p["blocks"])
    word_limit = int(options.get("wordsPerLesson", 220))
    minimum = int(options.get("minLessons", 150))
    if timing['planningMode'] == 'sessions':
        word_limit = (timing['sessionMinutes'] - timing['practiceMinutes']) * timing['readingWpm']
        minimum = 1
    # At least ~45 words per text lesson; short source material is never padded.
    target = max(math.ceil(total_words / word_limit), min(minimum, max(1, total_words // 60)))
    budget = max(80, min(word_limit, math.ceil(total_words / max(1, target))))
    lessons = []
    for ci, chapter in enumerate(chapters):
        end = chapters[ci+1]["startPage"] - 1 if ci+1 < len(chapters) else len(pages)
        items = []
        for page in pages[chapter["startPage"]-1:end]:
            if page['disposition'] != 'learning':
                continue
            for bi, b in enumerate(page["blocks"]):
                for ti, text in enumerate([b['text']] if page.get('layoutSensitive') else split_text(b["text"], budget)):
                    items.append({"id": f"{b['id']}-t{ti}", "text": text,
                                  "type": "question" if b.get('role') == 'question' else "text",
                                  "role": b.get('role', 'text') if ti == 0 else 'text',
                                  "page": page["number"], "bbox": b["bbox"], "source": page["source"]})
            # Insert illustration crops near their source location. A margin QR or
            # promotional drawing outside the main reading area is not a lesson figure.
            main = page.get('mainBounds', [0,0,page['width'],page['height']])
            figures = []
            with Image.open(output / page['image']) as image:
                # Join touching drawing parts (e.g. a circle and its stem) before
                # cropping. Preserve the caption width instead of slicing labels.
                visual_regions = []
                for raw in page.get('visuals', [])[:30]:
                    region = pdf.Rect(raw)
                    merged = True
                    while merged:
                        merged = False
                        for previous in list(visual_regions):
                            if (region + (-20,-20,20,20)).intersects(previous):
                                region |= previous
                                visual_regions.remove(previous)
                                merged = True
                    visual_regions.append(region)
                for fi, raw in enumerate(visual_regions):
                    if page.get('layoutSensitive'):
                        break
                    r = pdf.Rect(raw)
                    if not main[0] <= (r.x0+r.x1)/2 <= main[2] or max(r.width,r.height) < 22:
                        continue
                    r = pdf.Rect(min(main[0],r.x0),r.y0-18,max(main[2],r.x1),r.y1+18) & pdf.Rect(0,0,page['width'],page['height'])
                    if r.get_area() < 500 or r.get_area() > page['width']*page['height']*.7:
                        continue
                    sx,sy = image.width/page['width'],image.height/page['height']
                    clip = image.crop((int(r.x0*sx),int(r.y0*sy),math.ceil(r.x1*sx),math.ceil(r.y1*sy)))
                    asset = f"assets/figure-{page['number']:04d}-{fi+1:02d}.png"
                    clip.save(output/asset,optimize=True)
                    figures.append({'id':f"p{page['number']}-figure{fi}", 'type':'figure','role':'figure', 'text':'',
                                    'image':asset,'page':page['number'],'bbox':list(r),'source':'image'})
            for figure in figures:
                at = next((i for i,b in enumerate(items) if b['page']==page['number'] and b['bbox'][1]>figure['bbox'][1]),len(items))
                items.insert(at, figure)
            if not page["blocks"]:
                items.append({"id": f"p{page['number']}-scan", "text": "", "type": "source",
                              "page": page["number"], "bbox": [0, 0, page["width"], page["height"]], "source": "image"})
        groups, current, words = [], [], 0
        for item in items:
            w = count_words(item["text"])
            layout = pages[item['page']-1].get('layoutSensitive',False)
            page_break = bool(current and item['page'] != current[-1]['page'] and (layout or pages[current[-1]['page']-1].get('layoutSensitive',False)))
            # A heading belongs with the explanation that follows, never by itself.
            heading_break = item.get('role') == 'heading' and words >= max(65,budget*.6)
            if current and (page_break or (not layout and (heading_break or (words+w > budget*1.25 and words >= budget*.7 and current[-1].get('role') != 'heading'))) or item["type"] == "source"):
                groups.append(current)
                current, words = [], 0
            current.append(item)
            words += w
            if item["type"] == "source":
                groups.append(current)
                current, words = [], 0
        if current:
            if groups and sum(count_words(b['text']) for b in current) < 35 and current[0]['type'] != 'source':
                groups[-1].extend(current)
            else:
                groups.append(current)
        context_title = chapter['title']
        title_counts = Counter()
        for li, group in enumerate(groups):
            start, stop = group[0]["page"], group[-1]["page"]
            heading = next((b['text'].splitlines()[0].strip() for b in group if b.get('role')=='heading'),None)
            if heading:
                context_title = heading[:180]
            title_counts[context_title] += 1
            title = context_title + (f" - Part {title_counts[context_title]}" if title_counts[context_title]>1 else '')
            lessons.append({"id": f"lesson-{len(lessons)+1}", "chapterId": chapter["id"], "title": title,
                            "pageStart": start, "pageEnd": stop, "blocks": group, "questions": [],
                            "panels": [{"page": p["number"], "image": p["image"]} for p in pages[start-1:stop] if p['disposition']=='learning'],
                            "reviewed": False, "warnings": []})
    chapters = [ch for ch in chapters if any(l['chapterId']==ch['id'] for l in lessons)]
    if not lessons:
        raise ValueError('The selected chapter plan contains no learning content.')
    # Refine a few long lessons if block-boundary grouping undershoots the target.
    # Keep every character exactly once and require substantive text on both sides.
    while len(lessons) < target:
        eligible = [l for l in lessons if not any(pages[b['page']-1].get('layoutSensitive') for b in l['blocks'])]
        if not eligible:
            break
        candidate = max(eligible, key=lambda l: sum(count_words(b["text"]) for b in l["blocks"]))
        n = sum(count_words(b["text"]) for b in candidate["blocks"])
        if n < 90:
            break
        first, second, seen = [], [], 0
        for block in candidate["blocks"]:
            w = count_words(block["text"])
            if seen >= n // 2:
                second.append(block)
            elif seen + w <= n // 2:
                first.append(block)
            else:
                parts = split_text(block["text"], max(1, n // 2 - seen))
                first.append({**block, "text": parts[0]})
                rest = "".join(parts[1:])
                if rest:
                    second.append({**block, "id": block["id"] + f"-r{len(lessons)}", "text": rest})
            seen += w
        if not first or not second:
            break
        candidate["blocks"] = first
        other = {**candidate, "id": f"lesson-extra-{len(lessons)+1}", "title": candidate["title"] + " (continued)", "blocks": second}
        lessons.insert(lessons.index(candidate)+1, other)
        for lesson in (candidate, other):
            lesson["pageStart"] = min(b["page"] for b in lesson["blocks"])
            lesson["pageEnd"] = max(b["page"] for b in lesson["blocks"])
            lesson["panels"] = [{"page": p["number"], "image": p["image"]} for p in pages[lesson["pageStart"]-1:lesson["pageEnd"]] if p['disposition']=='learning']
    if timing['planningMode'] == 'sessions':
        lessons = plan_sessions(lessons, timing)
    # Use cropped source layout automatically when reflow would damage fractions,
    # equations or tables. Margin furniture is masked in these learning crops.
    for li, lesson in enumerate(lessons):
        sensitive = any(pages[b['page']-1].get('layoutSensitive') for b in lesson['blocks'])
        lesson['presentation'] = 'layout' if sensitive else 'text'
        if sensitive:
            for panel in lesson['panels']:
                page = pages[panel['page']-1]
                chapter_title = next(ch['title'] for ch in chapters if ch['id']==lesson['chapterId'])
                focused = [b for b in lesson['blocks'] if b['page']==panel['page'] and ' '.join(b['text'].split()).casefold()!=chapter_title.casefold()]
                boxes = [b['bbox'] for b in focused] or [b['bbox'] for b in lesson['blocks'] if b['page']==panel['page']]
                if not boxes:
                    continue
                bounds = pdf.Rect(boxes[0])
                for box in boxes[1:]:bounds |= pdf.Rect(box)
                bounds = (bounds + (-8,-6,8,6)) & pdf.Rect(0,0,page['width'],page['height'])
                if page.get('layoutSensitive'):
                    # A mathematical page is kept as one coherent learning region,
                    # retaining diagrams that have no extractable text labels.
                    bounds = pdf.Rect(max(0,min(60,bounds.x0)), max(0,bounds.y0),
                                      min(page['width'],max(page['width']-45,bounds.x1)),
                                      min(page['height'],max(bounds.y1,page['height']*.885)))
                with Image.open(output/panel['image']) as img:
                    from PIL import ImageDraw
                    clean = img.copy()
                    draw = ImageDraw.Draw(clean)
                    sx,sy=img.width/page['width'],img.height/page['height']
                    for entry in analysis['excluded']:
                        if entry['page']==panel['page'] and 'watermark' not in entry['reason'].lower():
                            x0,y0,x1,y1=entry['bbox']
                            # Never erase overlapping learning text with a broad mask.
                            er=pdf.Rect(entry['bbox'])
                            if not any((er & pdf.Rect(b)).get_area()>5 for b in boxes):
                                draw.rectangle((int(x0*sx),int(y0*sy),math.ceil(x1*sx),math.ceil(y1*sy)),fill=1)
                    crop=clean.crop((int(bounds.x0*sx),int(bounds.y0*sy),math.ceil(bounds.x1*sx),math.ceil(bounds.y1*sy)))
                    focus=f"assets/focus-{li+1:05d}-{panel['page']:04d}.png"
                    crop.save(output/focus,optimize=True)
                    panel['focusImage']=focus
                    panel['focusBounds']=list(bounds)
    warnings = []
    if timing['planningMode'] == 'sessions':
        warnings.append('Session duration is a planning estimate, not a measured learning time. Reading pace, equations, diagrams and textbook exercises need review. Short unit endings are not padded.')
    if timing['expectedUnits'] and timing['expectedUnits'] != len(chapters):
        warnings.append(f"UNIT COUNT MISMATCH: expected {timing['expectedUnits']}, found {len(chapters)}. Check the unit boundaries and re-import with a manual chapter plan.")
    if len(lessons) < minimum:
        warnings.append(f"Created {len(lessons)} lessons, below the requested {minimum}. The source is not padded or duplicated to meet a count.")
    source_bytes = source.read_bytes()
    course = {"schemaVersion": "astar-1", "id": output.name,
            "title": options.get("title") or source.stem, "subject": options.get("subject") or "General",
            "language": options.get("language", "eng"), "createdAt": datetime.now(timezone.utc).isoformat(),
            "source": {"filename": options.get("filename", source.name), "pages": len(pages),
                       "sha256": hashlib.sha256(source_bytes).hexdigest()},
            "chapters": chapters, "lessons": lessons,
            "report": {"words": total_words, "lessons": len(lessons), "requestedMinimum": minimum,
                       "chapterMethod": method, "warnings": warnings, "analysis": analysis,
                       "pages": [{k: p.get(k) for k in ("number", "image", "source", "ocrConfidence", "warnings", "issues", "disposition", "excludedReason", "columnOrder")} for p in pages]},
            "settings": {**timing, "wordsPerLesson": word_limit, "minLessons": minimum, "chapterPlan": options.get("chapterPlan", ""), "imageMode": options.get("imageMode", "dither"), "ocr": options.get("ocr", True)}}
    progress(len(pages), len(pages), 'Reconstructing source-grounded textbook objects')
    course['structure'] = reconstruct(raw_pages,pages,chapters)
    return assess_course(course)
