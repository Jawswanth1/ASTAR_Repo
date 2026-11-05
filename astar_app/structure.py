"""Source evidence and conservative, independently reviewable interpretation.

No answer generation. Numbered answers are only linked as candidates, never keys.
"""
import copy
import hashlib
import json
import math
import re
from collections import Counter

VERSION = 'astar-structure-1'
EXERCISE = re.compile(r'^\s*(?:exercise|excercise)\s*[-–—:]?\s*(\d+(?:\.\d+)*)', re.I)
SECTION = re.compile(r'^\s*(\d+\.\d+(?:\.\d+)*)\s+([A-Za-z].*)')
NUMBER = re.compile(r'^\s*(\d+)[.)]\s*(.*)')
SUB = re.compile(r'(?<!\w)(\([a-zivxl]+\)|[ivxl]+\))\s*', re.I)
STOP = re.compile(r'^(?:what we have discussed|summary|project work|do this|try these|think.*discuss|key points)',re.I)
KINDS = {'paragraph','section','exercise','example','solution','question','subquestion','option','answer','figure','table','caption'}

def evidence_hash(evidence):
    # JS JSON serializes 595.0 as 595. Canonicalize integral floats so a browser
    # round trip cannot look like a change to immutable source geometry.
    def canonical(value):
        if isinstance(value,float) and value.is_integer():return int(value)
        if isinstance(value,list):return [canonical(v) for v in value]
        if isinstance(value,dict):return {k:canonical(v) for k,v in value.items()}
        return value
    return hashlib.sha256(json.dumps(canonical(evidence),sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def reconstruct(raw_pages, analyzed_pages, chapters):
    """Keep unfiltered blocks; interpret retained learning and answer evidence."""
    pages=[]; objects=[]; current=None; exercise=None; section=None; example=None
    section_ids={}; answer_mode=False; previous_chapter=None; last_question=None
    def make(kind,refs,label='',parent=None,exercise_label=None):
        obj=dict(id=f'obj-{len(objects)+1}',kind=kind,label=label,source=refs,
                 chapterId=chapter_id,parentId=parent,exercise=exercise_label,
                 review=dict(status='unreviewed',note=''),warnings=[],links=[])
        objects.append(obj)
        return obj
    for raw, page in zip(raw_pages,analyzed_pages):
        number=raw['number']
        chapter_id=next((c['id'] for c in reversed(chapters) if c['startPage']<=number),None)
        if chapter_id!=previous_chapter:
            current=exercise=section=example=last_question=None;section_ids={};previous_chapter=chapter_id
        raw_blocks=[]
        for i,b in enumerate(raw['blocks']):
            raw_blocks.append(dict(id=f'p{number}-b{i}',text=b['text'],bbox=b['bbox'],
                lines=b.get('lines',[]),mathLayout=b.get('mathLayout',False)))
        pages.append(dict(number=number,width=raw['width'],height=raw['height'],
            image=raw.get('originalImage',raw['image']),method=raw['source'],
            disposition=page['disposition'],blocks=raw_blocks,
            inspection=dict(textCharacters=sum(len(b['text']) for b in raw_blocks),
                            visualRegions=len(raw.get('visuals',[])),ocrConfidence=raw.get('ocrConfidence'))))
        by_id={b['id']:b for b in raw_blocks}
        heading_text=' '.join(b['text'] for b in raw_blocks if b['bbox'][1]<raw['height']*.2)
        if re.search(r'\bSYLLABUS\b|ACADEMIC STANDARDS|CHILDREN.*INSTRUCTIONS',heading_text,re.I):
            answer_mode=False;current=exercise=section=example=last_question=None
        if re.search(r'\bAnswers\b|\bAnswer Key\b',heading_text,re.I):answer_mode=True
        # Excluded answer pages remain usable evidence; other excluded pages remain
        # in the raw layer but do not become learning objects.
        is_answer=answer_mode and ('Reference matter' in (page.get('excludedReason') or '') or re.search(r'\bAnswers\b',heading_text,re.I))
        if is_answer:chapter_id=None  # Physical position after chapter 15 is not subject membership.
        if page['disposition']=='excluded' and not is_answer:continue
        kept=page['blocks'] if not is_answer else [b for b in raw_blocks if b['bbox'][1]>raw['height']*.13 and b['bbox'][3]<raw['height']*.9 and 'SCERT  TELANGANA' not in b['text']]
        if is_answer and current and current['kind']!='answer':current=exercise=section=example=last_question=None
        for b in kept:
            original=by_id.get(b['id'])
            if not original:continue
            text=original['text']; offset=0
            for line_index,line in enumerate(text.splitlines(keepends=True)):
                value=line.rstrip('\r\n'); clean=value.strip()
                ref=dict(page=number,blockId=b['id'],start=offset,end=offset+len(value),bbox=b['bbox'])
                if line_index<len(original.get('lines',[])):
                    ref['bbox']=original['lines'][line_index]['bbox']
                offset+=len(line)
                if not clean:continue
                ex=EXERCISE.match(clean); sec=SECTION.match(clean); num=NUMBER.match(clean)
                examp=re.match(r'^Example\s+(\d+)\s*[:.]?',clean,re.I)
                caption=re.match(r'^(?:Fig\.?|Figure|Table)\s*(\d+(?:\.\d+)*)\b',clean,re.I)
                if ex:
                    exercise=make('exercise',[ref],ex[1],section['id'] if section else None,ex[1]);current=None;example=None;last_question=None
                elif examp and not is_answer:
                    example=make('example',[ref],examp[1],section['id'] if section else None);current=example;exercise=None;last_question=None
                elif sec and not is_answer:
                    label=sec[1]; parent=section_ids.get(label.rsplit('.',1)[0])
                    section=make('section',[ref],label,parent);section_ids[label]=section['id'];current=None;exercise=example=last_question=None
                elif STOP.match(clean) and not is_answer:
                    section=make('section',[ref],clean,section['id'] if section else None);current=None;exercise=example=last_question=None
                elif re.match(r'^Solutions?\s*:',clean,re.I) and example:
                    current=make('solution',[ref],'',example['id'])
                elif caption and len(clean.split())<25:
                    obj=make('caption',[ref],caption[1],current['id'] if current else None)
                    obj['warnings']=['Caption candidate; verify its figure/table relationship.']
                elif num and exercise and not (original.get('mathLayout') and re.match(r'^\s*\d+\)',clean)):
                    current=make('answer' if is_answer else 'question',[ref],num[1],exercise['id'],exercise['label']);last_question=current
                    current['warnings'].append('Numbered item detected by rules; boundaries and notation require source review.')
                elif current and current['kind'] in ('question','answer','example','solution'):
                    current['source'].append(ref)
                else:
                    current=None
                    parent=section['id'] if section else None
                    if objects and objects[-1]['kind']=='paragraph' and objects[-1]['parentId']==parent and objects[-1]['source'][-1].get('blockId')==b['id']:
                        objects[-1]['source'].append(ref)
                    else:make('paragraph',[ref],'',parent)
        # Preserve visual/table regions as located evidence, not guessed semantics.
        # Include vector bounds even on mathematical pages where the reader uses a full crop.
        for kind,regions in [('figure',raw.get('structureVisuals',raw.get('visuals',[]))),('table',raw.get('tables',[]))]:
            for region in regions:
                bbox=region['bbox'] if isinstance(region,dict) else region
                # PDF drawing objects can extend far outside the visible page.
                # Preserve only the visible intersection as a reviewable region.
                bbox=[max(0,bbox[0]),max(0,bbox[1]),min(raw['width'],bbox[2]),min(raw['height'],bbox[3])]
                if bbox[2]<=bbox[0] or bbox[3]<=bbox[1]:continue
                obj=make(kind,[dict(page=number,bbox=bbox)],'',None)
                obj['warnings']=['Detected region; compare with the complete original page.']
                if isinstance(region,dict):obj['cells']=region.get('cells',[])
    evidence=dict(pages=pages)
    raw_map={b['id']:b for p in pages for b in p['blocks']}
    for obj in list(objects):
        obj['text']='\n'.join(raw_map[r['blockId']]['text'][r['start']:r['end']] for r in obj['source'] if 'blockId' in r)
        # Subparts/options retain exact spans. Parent question remains intact too.
        if obj['kind'] == 'question':
            for r in obj['source']:
                t=raw_map[r['blockId']]['text'][r['start']:r['end']]
                marks=list(SUB.finditer(t))
                for i,m in enumerate(marks):
                    end=marks[i+1].start() if i+1<len(marks) else len(t)
                    child_ref={**r,'start':r['start']+m.start(),'end':r['start']+end}
                    is_option=bool(re.search(r'choose|select|which of|correct (?:answer|option)',obj['text'],re.I))
                    child=make('option' if is_option else 'subquestion',[child_ref],m[1],obj['id'],obj['exercise'])
                    child['chapterId']=obj['chapterId'];child['text']=t[m.start():end]
                    child['warnings']=['Marker segmentation is provisional; continuation lines may remain in the parent question.']
            if re.search(r'figure|diagram|table|graph',obj['text'],re.I):
                candidates=[x for x in objects if x['kind'] in ('figure','table') and any(r['page']==s['page'] for r in obj['source'] for s in x['source'])]
                for x in candidates:
                    obj['links'].append(dict(kind='visual-candidate',targetId=x['id'],status='unverified',reason='Same-page candidate; association requires review.'))
                if not candidates:obj['warnings'].append('Visual reference has no detected same-page candidate. Inspect source pages and link the correct figure manually.')
    for answer in [o for o in objects if o['kind']=='answer']:
        candidates=[q for q in objects if q['kind']=='question' and q['exercise']==answer['exercise'] and q['label']==answer['label']]
        if len(candidates)==1:
            answer['links'].append(dict(kind='answer-candidate',targetId=candidates[0]['id'],status='unverified',reason='Matching exercise and question number; NOT an approved answer key.'))
        else:answer['warnings'].append('No unique question mapping. Never use this entry for automatic grading.')
    return dict(version=VERSION,evidence=evidence,evidenceHash=evidence_hash(evidence),objects=objects,
        policy='Raw evidence is immutable. Interpretations are provisional until reviewed. Answer candidates are never automatic grading keys.',
        coverage=dict(pages=len(pages),types=dict(Counter(o['kind'] for o in objects))))

def attach_lesson_references(course):
    model=course.get('structure')
    if not model:return
    locations={}
    for lesson in course['lessons']:
        for b in lesson['blocks']:
            raw_id=re.sub(r'-t\d+(?:-r\d+)*$','',b['id'])
            locations.setdefault(raw_id,set()).add(lesson['id'])
    for obj in model['objects']:
        obj['lessonIds']=sorted({lesson for r in obj['source'] for lesson in locations.get(r.get('blockId'),[])})
    model['coverage']['types']=dict(Counter(o['kind'] for o in model['objects']))

def validate_structure(model,page_count,chapter_ids):
    if not isinstance(model,dict) or model.get('version')!=VERSION:raise ValueError('Unsupported structural model.')
    evidence=model.get('evidence',{})
    if not isinstance(evidence,dict):raise ValueError('Invalid extraction evidence.')
    if evidence_hash(evidence)!=model.get('evidenceHash'):raise ValueError('Source evidence checksum mismatch.')
    pages=evidence.get('pages',[]);objects=model.get('objects',[])
    if not isinstance(pages,list) or len(pages)!=page_count or not isinstance(objects,list) or len(objects)>250000:raise ValueError('Invalid structural coverage.')
    blocks={};dimensions={}
    def box(b,w,h):
        if not isinstance(b,list) or len(b)!=4 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in b) or b[2]<b[0] or b[3]<b[1]:raise ValueError('Invalid source bounds.')
        # PDF glyph bounds may extend slightly beyond a media box.
        if b[0]<-w or b[1]<-h or b[2]>2*w or b[3]>2*h:raise ValueError(f'Source bounds outside page: {b} on {w} x {h}.')
    for n,p in enumerate(pages,1):
        if not isinstance(p,dict) or not isinstance(p.get('blocks'),list):raise ValueError('Invalid evidence page.')
        if p.get('number')!=n or not 0<p.get('width',0)<20000 or not 0<p.get('height',0)<20000:raise ValueError('Invalid evidence page.')
        dimensions[n]=(p['width'],p['height'])
        if not re.fullmatch(r'assets/(?:original|page)-\d{4,5}\.png',p.get('image','')):raise ValueError('Invalid evidence image.')
        for b in p.get('blocks',[]):
            if not isinstance(b,dict) or not isinstance(b.get('id'),str):raise ValueError('Invalid evidence block.')
            if b.get('id') in blocks or not isinstance(b.get('text'),str) or len(b['text'])>100000:raise ValueError('Invalid evidence block.')
            box(b['bbox'],p['width'],p['height']);blocks[b['id']]=(n,b)
    ids=set()
    for o in objects:
        if not isinstance(o,dict):raise ValueError('Invalid structural object.')
        if not re.fullmatch(r'obj-\d+',o.get('id','')) or o['id'] in ids or o.get('kind') not in KINDS:raise ValueError('Invalid structural object.')
        ids.add(o['id'])
    for o in objects:
        if o.get('chapterId') is not None and o['chapterId'] not in chapter_ids:raise ValueError('Unknown structural chapter.')
        if o.get('parentId') and o['parentId'] not in ids:raise ValueError('Unknown structural parent.')
        refs=o.get('source',[])
        if not isinstance(refs,list) or not refs:raise ValueError('Structural object has no source.')
        parts=[]
        for r in refs:
            if not isinstance(r,dict):raise ValueError('Invalid source span.')
            if r.get('page') not in dimensions:raise ValueError('Invalid structural page.')
            box(r['bbox'],*dimensions[r['page']])
            if 'blockId' in r:
                if r['blockId'] not in blocks:raise ValueError('Unknown source block.')
                n,b=blocks[r['blockId']]
                if n!=r['page'] or not isinstance(r.get('start'),int) or not isinstance(r.get('end'),int) or not 0<=r['start']<=r['end']<=len(b['text']):raise ValueError('Invalid source text span.')
                parts.append(b['text'][r['start']:r['end']])
        if o.get('text')!='\n'.join(parts):raise ValueError('Extracted text must match source spans. Store corrections separately.')
        review=o.get('review',{})
        if not isinstance(review,dict) or review.get('status') not in ('unreviewed','checked','needs-correction') or not isinstance(review.get('note'),str) or len(review['note'])>5000:raise ValueError('Invalid structural review.')
        for key in ('label','correction'):
            if key in o and (not isinstance(o[key],str) or len(o[key])>100000):raise ValueError('Invalid structural correction.')
        if not isinstance(o.get('links'),list) or not isinstance(o.get('warnings'),list) or any(not isinstance(w,str) for w in o['warnings']):raise ValueError('Invalid structural links or warnings.')
        for link in o.get('links',[]):
            if not isinstance(link,dict):raise ValueError('Invalid source relationship.')
            if link.get('targetId') not in ids or link.get('status') not in ('unverified','checked','rejected'):raise ValueError('Invalid source relationship.')
    parents={o['id']:o.get('parentId') for o in objects}
    for ident in parents:
        seen=set();cursor=ident
        while cursor:
            if cursor in seen:raise ValueError('Structural parent cycle.')
            seen.add(cursor);cursor=parents.get(cursor)
    return model
