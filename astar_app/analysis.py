"""Document-wide layout analysis and evidence-based review triage, entirely local.

Exclusions are recorded, never erased from the source. Risk is a rule-based
extraction diagnostic, not a probability of factual correctness.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from statistics import median

VERSION = "2.0"
FRONT = re.compile(r"^(?:foreword|preface|acknowledg(?:e)?ments?|table of contents|contents|"
                   r"copyright(?: page)?|publication details|about (?:this book|the authors?)|"
                   r"list of (?:figures|tables)|contributors|textbook development committee|"
                   r"a note (?:for|to) (?:the )?teachers?|to the teacher|how to use this (?:book|textbook))\s*[:.]?$", re.I)
BACK = re.compile(r"^(?:bibliography|references|index|picture credits|credits|answers|answer key|solutions)\s*[:.]?$", re.I)
CHAPTER = re.compile(r"^(?:chapter|unit)\s+(?:\d+|[ivxlc]+)\b", re.I)
ADMIN = re.compile(r"\b(?:isbn(?:[- ]1[03])?|all rights reserved|reprint(?:ed)?\s+20\d\d|"
                   r"published by|printed (?:at|by|in)|copyright|publication division|"
                   r"subscribe|advertisement|scan (?:this |the )?(?:qr|code)|"
                   r"download (?:the |our )?app|visit (?:our |the )?website|"
                   r"teacher.?s edition|not for (?:sale|resale)|price\s*[:₹$£]|"
                   r"syllabus code|production team|typeset(?:ting)? by)\b", re.I)
LEARNING = re.compile(r"\b(?:activity|experiment|investigat\w*|worked example|example|exercise|"
                      r"question|definition|remember|key (?:idea|term)|did you know|think|"
                      r"figure|fig\.|diagram|table|observe|learning objectives?|try this|"
                      r"recall|vocabulary|glossary|hint|note that)\b", re.I)
STOP = set("the a an and or of to in on at is are was were be been being it this that these those "
           "for from with by as we you your our their them they its which what how why when where "
           "can could will would should has have had do does did not but also into about than "
           "each any all more most some such through using use used see page chapter section".split())


def words(text):
    return len(re.findall(r"\S+", text))


def terms(text):
    return {w for w in re.findall(r"[^\W\d_]{3,}", text.casefold()) if w not in STOP}


def signature(text):
    return re.sub(r"\s+", " ", re.sub(r"\d+", "#", text.casefold())).strip()


def issue(code, message, severity="medium", page=None):
    return {"code": code, "message": message, "severity": severity, "pages": [page] if page else []}


def analyze_pages(pages, bookmarks=()):
    """Tag blocks, remove clear non-learning material and resolve simple columns."""
    excluded = []
    sizes = Counter()
    repetitions = {}
    global_repetitions = {}
    for page in pages:
        for i, block in enumerate(page["blocks"]):
            block["id"] = f"p{page['number']}-b{i}"
            size = round(block.get("size", 0), 1)
            if words(block["text"]) >= 15 and size:
                sizes[size] += min(300, words(block["text"]))
            b = block["bbox"]
            edge = b[3] <= page["height"]*.12 or b[1] >= page["height"]*.90
            if edge and words(block["text"]) <= 18:
                repetitions.setdefault(signature(block["text"]), set()).add(page["number"])
            if words(block['text']) <= 10:
                global_repetitions.setdefault(signature(block['text']),set()).add(page['number'])
    body_size = sizes.most_common(1)[0][0] if sizes else 11
    repeat_min = 2 if len(pages)<=8 else 3
    first_chapter = next((p["number"] for p in pages if any(CHAPTER.match(b["text"].strip())
                          and b.get("size", 0) >= body_size*1.15 for b in p["blocks"])), None)
    numbered_bookmarks = [entry[2] for entry in bookmarks if re.search(r'(?:^|\b)ch(?:apter)?[\s_.-]*0*[1-9]\d*',entry[1],re.I)]
    if numbered_bookmarks:
        first_chapter = min(numbered_bookmarks)
    first_titles = {}
    for page in pages:
        for block in page['blocks']:
            if CHAPTER.match(block['text'].strip()) and block.get('size',0) >= body_size*1.2:
                first_titles.setdefault(block['text'].casefold().strip(),page['number'])
    in_front_section = None
    in_back_section = None

    def exclude(page, block, reason, category):
        excluded.append({"id": "excluded-" + block["id"], "page": page["number"],
                         "text": block["text"], "bbox": block["bbox"],
                         "reason": reason, "category": category, "restored": False})

    for page in pages:
        number, width, height = page["number"], page["width"], page["height"]
        page["issues"] = []
        page["disposition"] = "learning"
        page["excludedReason"] = None
        original = page["blocks"]
        page['chapterMarker'] = any(re.fullmatch(r'\s*(?:chapter\s*\d*|\d+\s*chapter)\s*',b['text'],re.I)
                                    and b['bbox'][1]<height*.25 for b in original)
        # Only standalone titles near the top count as front/back matter headings.
        top = [b for b in original if b["bbox"][1] < height*.38]
        front = next((b["text"].splitlines()[0].strip() for b in top
                      if FRONT.fullmatch(b["text"].splitlines()[0].strip())), None)
        back = next((b["text"].splitlines()[0].strip() for b in top
                     if BACK.fullmatch(b["text"].splitlines()[0].strip())), None)
        content = "\n".join(b["text"] for b in original)
        toc_rows = len(re.findall(r"(?:\.{3,}|\s{3,})\s*\d+\s*$", content, re.M))
        administrative = sum(bool(ADMIN.search(b["text"])) for b in original)
        early = number <= max(12, int(len(pages)*.18)) and (not first_chapter or number < first_chapter)
        reason = None
        if first_chapter and number < first_chapter and numbered_bookmarks:
            reason = f"Preliminary material before the first numbered chapter (PDF page {first_chapter})"
        elif front and early:
            reason = f"Front matter: {front}"
            in_front_section = front
        elif toc_rows >= 3 and early:
            reason = "Table of contents"
        elif early and administrative >= 2 and words(content) < 350:
            reason = "Publication and copyright page"
        elif first_chapter and number < first_chapter and words(content) < 65:
            reason = "Cover or title page before the first chapter"
        elif first_chapter and number < first_chapter and in_front_section:
            introduction = any(re.match(r'^(?:introduction|getting started|learning objectives)\b',b['text'],re.I)
                               and b.get('size',0)>=body_size*1.2 for b in top)
            if introduction:
                in_front_section = None
            else:
                reason = f"Front matter continuation: {in_front_section}"
        elif back and number > len(pages)*.65:
            reason = f"Reference matter: {back}"
            in_back_section = back
        elif in_back_section and not page['chapterMarker']:
            reason = f"Reference matter continuation: {in_back_section}"
        if not original and not page.get("visuals") and not page.get("hasInk", True):
            reason = "Blank page"
        if reason:
            page.update(disposition="excluded", excludedReason=reason)
            for block in original:
                exclude(page, block, reason, "page")
            page["blocks"] = []
            continue

        # Infer the main reading area from substantive paragraphs, not arbitrary margins.
        body = [b for b in original if words(b["text"]) >= 20 and b["bbox"][2]-b["bbox"][0] > width*.35]
        main_left = median([b["bbox"][0] for b in body]) if body else width*.10
        main_right = median([b["bbox"][2] for b in body]) if body else width*.90
        topic = terms(" ".join(b["text"] for b in body))
        kept = []
        for block in original:
            text, box = block["text"], block["bbox"]
            n = words(text)
            edge = box[3] <= height*.12 or box[1] >= height*.90
            page_number = bool(re.fullmatch(r"\s*(?:page\s*)?(?:\d+|[ivxlc]+)\s*", text, re.I))
            repeated = len(repetitions.get(signature(text), ())) >= repeat_min
            heading = (block.get("size", 0) >= body_size*1.2 and n <= 22) or bool(re.match(r"^\d+(?:\.\d+)+\s+\S", text))
            chapter_label = page['chapterMarker'] and box[1]<height*.2 and (bool(re.fullmatch(r'\s*(?:chapter\s*\d*|\d+\s*chapter)\s*',text,re.I)) or (text.strip().isdigit() and block.get('size',0)>body_size*2))
            if chapter_label:
                exclude(page,block,'Chapter navigation label; the chapter title is retained','furniture')
                continue
            # Keep prominent chapter titles; remove their small running-header copies.
            first_title = heading and CHAPTER.match(text.strip()) and first_titles.get(text.casefold().strip()) == number
            if edge and (page_number or (repeated and not first_title and not LEARNING.search(text) and not looks_like_question(text))) and n <= 18:
                exclude(page, block, "Repeated running header/footer or page number", "furniture")
                continue
            narrow = box[2]-box[0] < width*.29
            outside = box[2] <= main_left+8 or box[0] >= main_right-8
            marginal = narrow and outside and bool(body)
            promotional = bool(ADMIN.search(text)) or bool(re.fullmatch(r"\s*(?:https?://|www\.)\S+\s*", text))
            large_stamp = block.get('size',0)>=body_size*2.5 and (box[2]-box[0])*(box[3]-box[1])>width*height*.10
            watermark = (edge or large_stamp) and len(global_repetitions.get(signature(text),())) >= max(3,len(pages)*.55)
            if watermark and not first_title and not LEARNING.search(text) and not looks_like_question(text):
                exclude(page,block,'Repeated watermark or publisher label','furniture')
                continue
            if promotional and (marginal or edge or n < 25) and not LEARNING.search(text):
                exclude(page, block, "Publication, promotion, website or QR instruction", "nonlearning")
                continue
            overlap = len(terms(text) & topic)
            if marginal and not LEARNING.search(text) and n >= 6 and len(terms(text))>=3 and not block.get('mathLayout') and overlap == 0:
                # Geometry alone cannot prove irrelevance: preserve uncertain side notes.
                page["issues"].append(issue("ambiguous_margin", "A side note may be unrelated; it was retained to avoid losing learning material.", page=number))
            role = "heading" if heading else "question" if looks_like_question(text) else "text"
            kept.append({**block, "role": role})

        # Two substantial columns are learning content, not sidebars. Read each column
        # completely, using full-width headings as boundaries between regions.
        kept = sorted(kept, key=lambda b:(b['bbox'][1],b['bbox'][0]))
        candidates = [b for b in kept if words(b["text"]) >= 12]
        left = [b for b in candidates if b["bbox"][2] < width*.56]
        right = [b for b in candidates if b["bbox"][0] > width*.44]
        if left and right and min(sum(words(b['text']) for b in left), sum(words(b['text']) for b in right)) >= 35:
            if max(b['bbox'][2] for b in left) + 5 < min(b['bbox'][0] for b in right):
                full = sorted([b for b in kept if b not in left and b not in right and b['bbox'][2]-b['bbox'][0] > width*.55], key=lambda b:b['bbox'][1])
                ordered = []
                remaining = list(kept)
                for boundary in full + [{"bbox": [0, height+1, width, height+1]}]:
                    region = [b for b in remaining if b['bbox'][1] < boundary['bbox'][1]-2]
                    ordered.extend(sorted(region, key=lambda b:(0 if (b['bbox'][0]+b['bbox'][2])/2 < width/2 else 1, b['bbox'][1])))
                    remaining = [b for b in remaining if b not in region]
                    if boundary in remaining:
                        ordered.append(boundary); remaining.remove(boundary)
                kept = ordered + remaining
                page["columnOrder"] = "left column, then right column"
        page["blocks"] = kept
        page['layoutSensitive'] = sum(b.get('mathLayout',False) for b in kept) >= 2
        if len(page.get('visuals',[])) > 15:
            page['issues'].append(issue('complex_graphics','Dense graphics or a table may need a source-layout check.',page=number))
        page["mainBounds"] = [max(0, main_left-12), 0, min(width, main_right+12), height]
        if not kept:
            page["issues"].append(issue("missing_text", "No readable learning text was extracted. OCR or transcription is needed.", "high", number))
        if page.get("source") == "ocr" and page.get("ocrConfidence") is not None and page["ocrConfidence"] < 80:
            page["issues"].append(issue("weak_ocr", f"OCR confidence is low ({page['ocrConfidence']}%).", "high", number))
        bad = content.count("\ufffd") + content.count("\u25a0")
        if bad:
            page["issues"].append(issue("broken_characters", "Missing or undecodable characters were found.", "high", number))
        if any("OCR failed" in w for w in page.get("warnings", [])):
            page["issues"].append(issue("ocr_failed", "OCR failed on this page; the source image is available.", "high", number))
    return {"version": VERSION, "bodyFontSize": body_size, "excluded": excluded}


def looks_like_question(text):
    # A rhetorical question in a long explanation is not an entire exercise.
    first = text.strip().splitlines()[0] if text.strip() else ""
    return bool(re.match(r"^(?:\d+[.)]\s*|[Qq](?:uestion)?\s*\d+\s*[:.)]?\s*)?(?:explain|describe|discuss|calculate|write|compare|why\b|how\b|what\b|state\b|list\b|give reasons|find\b|choose\b)", first, re.I)
                or ("?" in text and words(text) < 55 and re.match(r"^\s*\d+[.)]", text)))


def assess_course(course):
    """Recompute triage after conversion or editing; human review remains distinct."""
    from .structure import attach_lesson_references
    attach_lesson_references(course)
    page_map = {p['number']: p for p in course['report']['pages']}
    for lesson in course['lessons']:
        issues = []
        for number in {b['page'] for b in lesson['blocks']}:
            for item in page_map.get(number, {}).get('issues', []):
                if lesson.get('presentation')=='layout' and item['code'] in ('broken_characters','complex_graphics'):
                    continue
                if not any(i['code'] == item['code'] and i['pages'] == item['pages'] for i in issues):
                    issues.append(item)
        text = ' '.join(b['text'] for b in lesson['blocks'])
        n = words(text)
        if not n:
            issues.append(issue('image_only', 'This lesson is image-only; searchable reading text is unavailable.', 'high', lesson['pageStart']))
        elif n < 35 and lesson.get('presentation')!='layout' and not all(b['type'] in ('question', 'figure') for b in lesson['blocks']):
            issues.append(issue('fragment', 'This lesson may be an isolated heading or a short fragment.', 'medium', lesson['pageStart']))
        if lesson.get('presentation')!='layout' and (re.search(r'(?:\b\w\s+){10,}', text) or (n > 20 and len(text) / max(1,n) < 2.3)):
            issues.append(issue('garbled_text', 'Unusually fragmented text suggests an extraction or font problem.', 'high', lesson['pageStart']))
        if any(b.get('role') == 'formula' for b in lesson['blocks']):
            issues.append(issue('formula', 'A complex formula needs comparison with its source.', 'medium', lesson['pageStart']))
        severity = 'high' if any(i['severity']=='high' for i in issues) else 'medium' if issues else 'low'
        risk = min(100, sum(60 if i['severity']=='high' else 25 for i in issues))
        lesson['quality'] = {'severity': severity, 'risk': risk,
                             'status': 'reviewed' if lesson['reviewed'] else 'attention' if issues else 'auto' if course['report'].get('analysis') else 'legacy',
                             'issues': issues}
        lesson['warnings'] = [i['message'] for i in issues]
    pending = [l for l in course['lessons'] if l['quality']['status']=='attention']
    course['report']['quality'] = {'automatic': sum(l['quality']['status']=='auto' for l in course['lessons']),
        'reviewed': sum(l['reviewed'] for l in course['lessons']), 'attention': len(pending),
        'high': sum(l['quality']['severity']=='high' for l in pending),
        'queue': [l['id'] for l in sorted(pending, key=lambda l:(-l['quality']['risk'], l['pageStart']))]}
    return course
