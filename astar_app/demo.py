"""Chapter-one demonstration, with an explicitly curated SCERT reference plan.

New books use detected concept headings, not arbitrary equal page partitions.
Unverified interpretations and native PDF transcription defects are reported.
The unmodified PDF, page evidence and exact source regions remain authoritative.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import threading
import uuid
import zipfile
from pathlib import Path

import pymupdf as pdf
from PIL import Image

from .converter import learning_pixmap
from .epaper import menu_frame, pack_frame, source_frames, text_frames
from .storage import atomic_json

ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA = ROOT / 'demo-data'
SCERT_HASH = '145db19b3157b941900f22e619c9e2c0bac13b712bf8928bc70ae2af6123ed02'
BUILD_LOCK = threading.Lock()
VERSION = 2

# Page coordinates refer to PRINTED pages, not physical PDF positions.
PLAN = [
    dict(title='Meet rational numbers', short='Rational numbers', sections=['1.0','1.1'],
         concepts=['rational number','integer','fraction','addition','subtraction','multiplication','division'],
         start=[1,110], end=[5,630],
         intro='A whole number is not enough to describe every quantity. Explore rational numbers, then recall the four operations.',
         learn=[('A larger number family','A rational number has the form p/q, where p and q are integers and q is not zero. Natural numbers, whole numbers and integers can all be written in this form.'),
                ('Multiply and divide','To multiply, multiply the numerators and multiply the denominators. To divide by a nonzero rational number, multiply by its reciprocal. Preserve the signs.'),
                ('Worked calculation','ASTAR worked explanation: (-10/21) x (14/25) = -140/525 = -4/15. Compare the original worked calculation on printed page 4.')],
         refs=['2','3-5','4'], example=[4,120,423], activity=[2,518,746], checkpoint='ex-1.1-8',
         recap='Rational numbers include integers and fractions. A denominator cannot be zero. Multiplication uses numerator and denominator products; division uses the reciprocal.'),
    dict(title='Patterns in operations', short='Operation properties', sections=['1.2.1','1.2.2','1.2.3'],
         concepts=['closure','commutative','associative','order','grouping'],start=[5,630],end=[16,310],
         intro='Investigate what changes when you swap or regroup numbers. Compare addition, subtraction, multiplication and division.',
         learn=[('Closure','Adding, subtracting or multiplying two rational numbers gives another rational number. Division requires a nonzero divisor. The book describes Q as not closed under division because zero belongs to Q.'),
                ('Order and grouping','Addition and multiplication are commutative and associative. Subtraction and division do not have these properties in general. A counterexample is enough to disprove a general property.'),
                ('Test a claim','ASTAR worked explanation: (1 - 2) - 3 = -4, while 1 - (2 - 3) = 2. Changing the grouping changes the result, so subtraction is not associative.')],
         refs=['6-8','9-15','14'],example=[14,166,527],activity=[16,120,305],checkpoint='ex-1.1-11',
         recap='Ask three different questions: Is the result in the set? Does order matter? Does grouping matter? Use a nonzero divisor whenever you divide.'),
    dict(title='Identity, inverse & distribution', short='Identity and inverse',sections=['1.2.4','1.2.5','1.2.6','1.3'],
         concepts=['identity','inverse','reciprocal','distributive','distributivity'],start=[16,310],end=[23,638],
         intro='Learn which numbers leave a value unchanged, which undo an operation, and how multiplication distributes across a sum.',
         learn=[('Two identities','Adding zero leaves a rational number unchanged: a + 0 = a. Multiplying by one leaves it unchanged: a x 1 = a. Zero is the additive identity; one is the multiplicative identity.'),
                ('Two inverses','A number and its additive inverse sum to zero. Nonzero rational numbers have reciprocals whose product with the original number is one. Zero has no reciprocal.'),
                ('Distribute multiplication','ASTAR notation guide: a x (b + c) = a x b + a x c. The same pattern works with subtraction. The original worked example on page 19 uses 2/5, 1/2 and 3/4.')],
         refs=['16-17','17-18','18-19'],example=[19,120,302],activity=[18,443,611],checkpoint='ex-1.1-2',
         recap='Identity preserves a value; inverse takes it to the identity. Distributing multiplication can simplify a calculation. Never take the reciprocal of zero.'),
    dict(title='Find a place on the line', short='The rational number line',sections=['1.4','1.5'],
         concepts=['number line','between','mean','represent','density','smaller'],start=[23,638],end=[28,581],
         intro='Locate positive and negative fractions on the number line. Then find more rational numbers between two given values.',
         learn=[('Equal parts','Divide each unit into as many equal parts as the denominator requires. Count the parts using the numerator. Negative rational numbers lie to the left of zero.'),
                ('Between two numbers','For distinct rational numbers a and b, their mean (a + b)/2 lies between them. Repeating the method gives more numbers. Equivalent fractions with larger denominators offer another method.'),
                ('A first midpoint','ASTAR worked explanation: between 2 and 3 is (2 + 3)/2 = 5/2. Between 2 and 5/2 is 9/4. The original diagrams and calculations are on page 26.')],
         refs=['24-25','26-27','26'],example=[25,119,315],activity=[25,501,743],checkpoint='ex-1.2-5',
         recap='Use equal intervals on a number line. Between any two distinct rational numbers there are infinitely many rational numbers. A mean supplies one of them.'),
    dict(title='Fractions meet decimals',short='Fractions and decimals',sections=['1.6','1.7'],
         concepts=['decimal','terminating','recurring','repeating','period','periodicity'],start=[28,581],end=[36,748],
         intro='Read terminating and recurring decimals, then convert them back into rational numbers. Keep recurring bars visible in the original source.',
         learn=[('Divide to get decimals','A rational number has a terminating decimal or a non-terminating recurring decimal. In a recurring decimal, a digit or group of digits repeats in the same order.'),
                ('Period and periodicity','The repeating group is called the period. Its number of digits is the periodicity. For 0.12757575..., the period is 75 and the periodicity is 2.'),
                ('Return to a fraction','ASTAR worked explanation: let x = 0.545454... . Then 100x = 54.545454... . Subtract x to obtain 99x = 54, so x = 54/99 = 6/11. The textbook method appears on page 33.')],
         refs=['29-31','31','32-34'],example=[33,320,571],activity=[31,576,746],checkpoint='ex-1.3-11',
         recap='Distinguish a finite decimal from a repeating one. Use a power of ten for terminating decimals. For recurring decimals, align repeating digits, subtract and solve for the fraction.')
]

# Every numbered exercise question is explicitly assigned by concept. Exercise
# 1.3 deliberately returns arithmetic problems to lesson 1, not lesson 5.
EXERCISES = [
    (22,'1.1',[(1,255,477,3),(2,477,542,3),(3,542,744,3)]),
    (23,'1.1',[(4,120,165,1),(5,165,204,3),(6,204,274,2),(7,274,317,2),
       (8,317,378,1),(9,378,422,1),(10,422,464,1),(11,464,484,2),
       (12,484,542,3),(13,542,638,3)]),
    (28,'1.2',[(1,292,356,4),(2,356,403,4),(3,403,441,4),(4,441,469,4),
       (5,469,531,4),(6,531,580,4)]),
    (35,'1.3',[(1,168,235,5),(2,235,305,5),(3,305,364,1),(4,364,407,1),
       (5,407,447,1),(6,447,504,1),(7,504,548,1),(8,548,585,1),
       (9,585,627,1),(10,627,671,1),(11,671,747,5)])
]

# Embedded prompts and activities are catalogued as coherent source groups.
# Subparts stay inside their original parent, preserving their printed labels.
EMBEDDED = [
 (1,270,440,'Introduction: pens',1),(1,465,746,'Introduction: temperature investigation',1),
 (2,120,216,'Opening questions',1),(2,518,746,'Do This: number families',1),
 (3,126,200,'Try These 1',1),(3,200,333,'Try These 2',1),(3,422,564,'Solve (i)-(v)',1),
 (4,424,526,'Do this: multiplication (i)-(iv)',1),
 (5,120,172,'Write multiplicative inverses',1),(5,523,626,'Do this: division (i)-(iv)',1),
 (6,121,404,'Complete the closure table',2),(6,520,640,'Check addition examples',2),
 (7,270,365,'Check subtraction (i)-(ii)',2),(7,556,646,'Check multiplication and discuss',2),
 (8,222,348,'Check division examples',2),(8,350,506,'Why division by zero is undefined',2),
 (8,510,560,'Try These: integer division',2),(8,572,747,'Do This: closure table',2),
 (9,220,746,'Complete commutativity tables',2),
 (10,310,492,'Check commutative addition',2),(10,645,744,'Check subtraction',2),
 (11,234,302,'Check multiplication',2),(11,380,508,'Check division order',2),
 (11,553,746,'Do This: commutative table',2),
 (12,235,618,'Complete associativity tables',2),(13,120,453,'Integer associativity table',2),
 (13,682,745,'Check the two sums',2),(14,256,528,'Verify subtraction grouping',2),
 (14,570,744,'Verify multiplication grouping',2),(15,120,315,'Check multiplication examples',2),
 (15,470,745,'Verify division grouping',2),(16,120,305,'Do This: associative table',2),
 (16,328,360,'Find the additive identity',3),(16,537,560,'Natural number identity?',3),
 (16,598,746,'Fill blanks: the role of 1',3),(17,172,200,'Identity for integers and wholes',3),
 (17,387,535,'Additive inverse blanks',3),(17,668,745,'Find a multiplicative inverse',3),
 (18,120,282,'Fill boxes: multiplicative inverses',3),
 (18,471,524,'Think, discuss and write 1',3),(18,524,544,'Think, discuss and write 2',3),
 (18,544,610,'Think, discuss and write 3',3),(18,665,745,'Verify distributivity',3),
 (19,301,441,'Verify distributive subtraction',3),(19,530,746,'Do These: additive table',3),
 (20,121,305,'Complete multiplicative table',3),
 (23,639,746,'Number-line opening question',4),(24,120,338,'Discuss number-line families',4),
 (25,501,674,'Try These: labelled number lines (i)-(ii)',4),
 (25,679,745,'Do This (i): represent -13/5',4),
 (26,145,231,'Natural numbers and integers between',4),(27,143,186,'Hundred rational numbers?',4),
 (29,545,620,'Try decimal conversions',5),(30,673,745,'Try recurring conversions',5),
 (31,514,567,'Period and periodicity blanks',5),(31,576,746,'Think and Discuss 1 (i)-(iv)',5),
 (34,659,746,'Think Discuss and Write: decimals',5),(36,482,747,'Can you find? Unit-square investigation',4)
]


def source_image(page, rect, scale=1.7):
    pix, removed = learning_pixmap(page, scale)
    image = Image.frombytes('L', (pix.width, pix.height), pix.samples)
    box = tuple(round(v*scale) for v in rect)
    return image.crop(box), removed


def find_boundaries(doc, start=None, end=None):
    if start is not None and end is not None:
        start, end = int(start), int(end)
        if not 1 <= start <= end <= len(doc):
            raise ValueError('Chapter boundaries must be within the PDF (1-based, inclusive).')
        return start, end, 'User-specified physical PDF pages; verify against the book.'
    toc = doc.get_toc()
    ch1 = next((t for t in toc if re.search(r'\bch(?:apter)?[\s_.-]*0*1\b',t[1],re.I)), None)
    ch2 = next((t for t in toc if re.search(r'\bch(?:apter)?[\s_.-]*0*2\b',t[1],re.I)), None)
    if ch1 and ch2 and ch2[2] > ch1[2]:
        return ch1[2], ch2[2]-1, 'PDF chapter bookmarks; source review required.'
    # Fail closed rather than assume the first page is Chapter 1 or include Ch 2.
    raise ValueError('No reliable Chapter 1 / Chapter 2 bookmark pair. Enter the first and last PDF page of Chapter 1.')


def generic_plan(doc, first, last):
    headings=[]
    for number in range(first,last+1):
        for b in doc[number-1].get_text('dict')['blocks']:
            for line in b.get('lines',[]):
                text=' '.join(s['text'] for s in line['spans']).strip()
                if re.match(r'^1\.\d+\s+[A-Za-z]',text) and len(text)<130:
                    headings.append((number,line['bbox'][1],text))
    # Preserve top-level concepts as the indivisible units of planning.
    if len(headings)<2:
        raise ValueError('Not enough reliable concept headings to plan lessons. This book needs a curated concept plan; no arbitrary page split was made.')
    n=min(5,len(headings))
    groups=[headings[i*len(headings)//n:(i+1)*len(headings)//n] for i in range(n)]
    result=[]
    for i,group in enumerate(groups):
        begin=[first,110] if i==0 else list(group[0][:2])
        finish=list(groups[i+1][0][:2]) if i+1<n else [last,doc[last-1].rect.height-55]
        result.append(dict(title=group[0][2],short=f'Concept lesson {i+1}',sections=[h[2] for h in group],
            concepts=re.findall(r'[a-z]{4,}',' '.join(h[2] for h in group).lower()),
            start=begin,end=finish,intro='Read the original source sections below. This automatically proposed concept grouping needs teacher review.',
            learn=[],refs=[],example=None,activity=None,checkpoint=None,
            recap='Review the original definitions, examples and questions. Record any unclear extraction before using this lesson for teaching.'))
    return result


def build_demo(source, directory, options=None, progress=None):
    options=options or {}
    progress=progress or (lambda *args:None)
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    source=Path(source)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    curated=digest==SCERT_HASH
    if source.resolve() != (directory/'source.pdf').resolve():
        shutil.copyfile(source,directory/'source.pdf')
    frames_dir=directory/'frames'; frames_dir.mkdir(exist_ok=True)
    evidence=directory/'evidence'; evidence.mkdir(exist_ok=True)
    with pdf.open(directory/'source.pdf') as doc:
        if doc.needs_pass:
            raise ValueError('Use an unlocked PDF.')
        if len(doc)>2000:
            raise ValueError('Maximum 2,000 PDF pages.')
        if curated:
            first,last,boundary_note=13,48,'Verified: contents printed 1-36; Chapter 2 starts PDF page 49.'
            plan=PLAN
            metadata=dict(title='Rational Numbers',book='Mathematics · Class VIII',publisher='SCERT Telangana',
                edition='2020-21 impression; first published 2013',className='VIII',subject='Mathematics',ncert=False)
        else:
            first,last,boundary_note=find_boundaries(doc,options.get('start'),options.get('end'))
            plan=generic_plan(doc,first,last)
            front='\n'.join(doc[i].get_text() for i in range(min(first,8)))
            metadata=dict(title='Chapter 1',book=options.get('title') or doc.metadata.get('title') or source.stem,
                publisher='NCERT (detected; verify)' if re.search(r'\bNCERT\b|National Council of Educational Research',front,re.I) else 'Not verified',
                edition='Not verified',className='Not verified',subject='Not verified',ncert=bool(re.search(r'\bNCERT\b',front)))
        if last-first+1>100:
            raise ValueError('Chapter scope exceeds 100 pages. Check the Chapter 1 boundaries before importing.')
        course=dict(id=directory.name,version=VERSION,source={**metadata, 'filename':options.get('filename',source.name),
            'sha256':digest,'pdfPages':len(doc),'first':first,'last':last,'boundaryNote':boundary_note,
            'printedFirst':1 if curated else None,'printedLast':36 if curated else None},
            curated=curated,lessons=[],questions=[],screens={},sourcePages=[],
            report=dict(extractionFailures=[],transcriptionWarnings=[],layoutIssues=[],
                excluded=f'All PDF pages outside {first}-{last}, including Chapter 2.',
                questionCatalogue='Curated source-region groups; original subparts retained in each parent.' if curated else 'Provisional detected prompt groups; completeness requires teacher review.',
                timings='Five 30-minute core routes. Reading all source tiles and solving all exercises requires additional time.' if curated else 'Proposed timing; requires teacher review.',
                review='Source wording and notation are authoritative in the linked original regions. Search text is native PDF extraction, not a verified mathematical transcription.',
                sourceRender='Only an isolated text-only diagonal publisher stamp may be suppressed in learning crops. Unmodified PDF and full-colour evidence pages are retained.'))
        raw_pages={}
        page_cache={}
        def render_page(number):
            if number not in page_cache:
                page=doc[number-1]
                if page.rect.width*page.rect.height>2_000_000:
                    raise ValueError(f'PDF page {number} has unsupported page dimensions.')
                image,removed=source_image(page,[0,0,page.rect.width,page.rect.height])
                page_cache[number]=(image,removed)
            return page_cache[number][0]

        def store_frame(frame,kind,title,source_ref=None,**extra):
            sid=f's{len(course["screens"])+1:05d}'
            result=frame.save(frames_dir/f'{sid}.png')
            (frames_dir/f'{sid}.bin').write_bytes(pack_frame(result))
            course['screens'][sid]=dict(id=sid,kind=kind,title=title,source=source_ref,**extra)
            return sid

        def add_text(title,text,label='ASTAR explanation',ref=None,kind='explanation'):
            return [store_frame(f,kind,title,ref,text=text,origin='ASTAR-generated')
                    for f in text_frames(title,text,label)]

        def region(number,y0,y1,title,kind='original',x0=30,x1=None):
            page=doc[number-1]
            x1=x1 or page.rect.width-45
            rect=[x0,max(0,y0),x1,min(page.rect.height,y1)]
            full=render_page(number)
            image=full.crop(tuple(round(v*1.7) for v in rect))
            printed=number-12 if curated else None
            ref=dict(pdfPage=number,printedPage=printed,bbox=rect)
            label=f'SCERT p.{printed} / PDF {number}' if curated else f'Original / PDF {number}'
            return [store_frame(f,kind,title,ref,tile=tile,origin='Original textbook')
                    for f,tile in source_frames(image,title,label)]

        # Extract and catalogue questions BEFORE lesson assembly.
        progress(0,last-first+1,'Extracting Chapter 1 and cataloguing questions')
        for number in range(first,last+1):
            page=doc[number-1]
            try:
                text=page.get_text(sort=True)
                raw_pages[number]=text
                (evidence/f'page-{number:04d}.txt').write_text(text,encoding='utf8')
                page.get_pixmap(matrix=pdf.Matrix(1.25,1.25)).save(evidence/f'page-{number:04d}.png')
                render_page(number)
                if len(re.sub(r'\s','',text))<50:
                    course['report']['extractionFailures'].append(dict(pdfPage=number,reason='Insufficient native text; source page preserved. No OCR was silently inferred.'))
                if '\ufffd' in text:
                    course['report']['transcriptionWarnings'].append(dict(pdfPage=number,reason='Replacement glyph in native PDF extraction. Use source image.'))
            except Exception as exc:
                course['report']['extractionFailures'].append(dict(pdfPage=number,reason=str(exc)))
            progress(number-first+1,last-first+1,f'Read PDF page {number}; Chapter 2 excluded')
        if curated:
            for printed,exercise,entries in EXERCISES:
                for number,y0,y1,lesson in entries:
                    qid=f'ex-{exercise}-{number}'
                    course['questions'].append(dict(id=qid,number=str(number),exercise=exercise,
                        label=f'Exercise {exercise} · Q{number}',type='Reasoning' if (exercise,number) in [('1.1',11),('1.1',13)] else 'Constructed response / subparts',
                        lesson=lesson,prerequisites=([2] if exercise=='1.1' and number in (1,3,5) else [1] if lesson>1 else []),
                        subsection=plan[lesson-1]['sections'],concepts=plan[lesson-1]['concepts'],
                        pdfPage=printed+12,printedPage=printed,bbox=[78,y0,515,y1],
                        rationale='Arithmetic operations, not decimal conversion.' if exercise=='1.3' and 3<=number<=10 else 'Assigned to the lesson teaching the required concepts.',
                        placement='checkpoint' if qid in [p['checkpoint'] for p in plan] else 'assessment',
                        note='Exercise 1.3 Q5 also uses solving a simple equation (prior knowledge).' if exercise=='1.3' and number==5 else '',
                        transcription='Native extraction: fractions and recurring bars require the linked source region.'))
            for index,(printed,y0,y1,label,lesson) in enumerate(EMBEDDED):
                course['questions'].append(dict(id=f'embedded-{index+1}',number=label,exercise=None,label=label,
                    type='Activity / embedded prompt group',lesson=lesson,prerequisites=[1] if lesson>1 else [],
                    subsection=plan[lesson-1]['sections'],concepts=plan[lesson-1]['concepts'],pdfPage=printed+12,
                    printedPage=printed,bbox=[30,y0,550,y1],rationale='Linked to its teaching subsection; original subparts stay together.',
                    placement='lesson practice',transcription='Native extraction; original region is authoritative.'))
            # Side callout on printed page 19 has two original numbered prompts.
            for no,y0,y1 in [(1,322,361),(2,370,407)]:
                course['questions'].append(dict(id=f'distribute-{no}',number=str(no),exercise=None,
                    label=f'Try these: distributivity ({no})',type='Numerical',lesson=3,prerequisites=[1],
                    subsection=['1.3'],concepts=['distributivity'],pdfPage=31,printedPage=19,bbox=[350,y0,584,y1],
                    rationale='Requires distributive multiplication.',placement='lesson practice',transcription='Use original notation.'))
        else:
            for number in range(first,last+1):
                for block in doc[number-1].get_text('blocks'):
                    t=block[4]
                    if '?' in t or re.match(r'\s*(?:\d+[.)]|[A-Z][a-z]+.*(?:following|blanks))',t):
                        if block[1]<100 or block[3]>doc[number-1].rect.height-50:continue
                        terms=set(re.findall(r'[a-z]{4,}',t.lower()))
                        scores=[len(terms & set(p['concepts'])) for p in plan]
                        lesson=scores.index(max(scores))+1 if max(scores)>0 else next((i+1 for i,p in reversed(list(enumerate(plan))) if number>=p['start'][0]),1)
                        course['questions'].append(dict(id=f'detected-{len(course["questions"])+1}',number=(re.match(r'\s*(\d+)[.)]',t) or [None,'Unnumbered'])[1],
                            label='Detected source prompt',exercise=None,type='Unverified source group',lesson=lesson,
                            prerequisites=[],subsection=plan[lesson-1]['sections'],concepts=plan[lesson-1]['concepts'],
                            pdfPage=number,printedPage=None,bbox=list(block[:4]),rationale='Lexical concept match; teacher verification required.',
                            placement='assessment',transcription='Unverified native PDF extraction.'))
        for q in course['questions']:
            q['text']=doc[q['pdfPage']-1].get_text(clip=pdf.Rect(q['bbox']),sort=True).strip()
            q['screens']=region(q['pdfPage'],q['bbox'][1],q['bbox'][3],
                f'Exercise {q["exercise"]} Q{q["number"]}' if q['exercise'] else 'Textbook investigation',
                kind='question',x0=q['bbox'][0],x1=q['bbox'][2])
            for sid in q['screens']:course['screens'][sid]['questionId']=q['id']

        for index,p in enumerate(plan):
            lid=index+1
            timing=[dict(section='Introduction',minutes=2),dict(section='Concept learning',minutes=14),
                dict(section='Example / activity',minutes=7),dict(section='Checkpoint',minutes=4),dict(section='Recap',minutes=3)]
            lesson=dict(id=lid,title=p['title'],short=p['short'],sections=p['sections'],concepts=p['concepts'],
                timing=timing,minutes=30,core=[],practice=[q['id'] for q in course['questions'] if q['lesson']==lid],
                pages=[p['start'][0],p['end'][0]],sourceScreens=[])
            lesson['core']+=add_text(f'Lesson {lid} / Introduction',p['intro'],'ASTAR lesson guide / 2 min',kind='introduction')
            for k,(title,text) in enumerate(p['learn']):
                lesson['core']+=add_text(title,text,f'ASTAR explanation / source pp.{p["refs"][k]}',
                    dict(printedPages=p['refs'][k]),kind='concept')
            if p['example']:
                printed,y0,y1=p['example']
                lesson['core']+=region(printed+12,y0,y1,'Original worked example')
            if p['activity']:
                printed,y0,y1=p['activity']
                # Reuse the catalogue's original activity screens if bounds match.
                found=next((q for q in course['questions'] if q['pdfPage']==printed+12 and abs(q['bbox'][1]-y0)<8 and abs(q['bbox'][3]-y1)<12),None)
                lesson['core']+=found['screens'] if found else region(printed+12,y0,y1,'Original textbook activity','activity')
            if p['checkpoint']:
                q=next(q for q in course['questions'] if q['id']==p['checkpoint'])
                lesson['core']+=add_text('Checkpoint / 4 minutes','Work in your notebook. Read all source tiles before answering. SELECT opens the action menu to record your attempt. Answers are not automatically graded.','ASTAR learning instruction',kind='instruction')
                lesson['core']+=q['screens']
            lesson['core']+=add_text('Recap / 3 minutes',p['recap'],'ASTAR recap / not a textbook quote',kind='recap')
            lesson['core']+=add_text('Lesson complete','Explain the key idea in your own words. SELECT and choose Mark lesson complete. Additional original questions are available in lesson practice and the chapter assessment.','ASTAR learning instruction',kind='completion')
            course['lessons'].append(lesson)

        # Full page source archive, individually tiled at a readable native scale.
        # Nothing from the chapter, including diagrams/tables/examples, is omitted.
        for number in range(first,last+1):
            if number not in page_cache:continue
            page=doc[number-1]
            screens=region(number,0,page.rect.height,'Original chapter archive','source',x0=0,x1=page.rect.width)
            course['sourcePages'].append(dict(pdfPage=number,printedPage=number-12 if curated else None,
                evidence=f'evidence/page-{number:04d}.png',characters=len(raw_pages.get(number,'')),screens=screens,
                nativeText=raw_pages.get(number,'')))
            if curated:
                printed=number-12
                for l,p in zip(course['lessons'],plan):
                    if p['start'][0]<=printed<=p['end'][0]:
                        y0=p['start'][1] if printed==p['start'][0] else 110
                        y1=p['end'][1] if printed==p['end'][0] else page.rect.height-94
                        if y1>y0:l['sourceScreens']+=region(number,y0,y1,'Original lesson archive','source')
            else:
                for l,p in zip(course['lessons'],plan):
                    if p['start'][0]<=number<=p['end'][0]:l['sourceScreens']+=screens
        if not curated:
            for lesson in course['lessons']:
                # A provisional import must still teach from the original pages,
                # rather than showing only generated introduction/recap screens.
                lesson['core']=lesson['core'][:1]+lesson['sourceScreens']+lesson['core'][1:]
        course['assessment']=[q['id'] for q in course['questions'] if q['placement']=='assessment']
        course['report'].update(framebuffer=dict(width=400,height=300,mode='1',bodyFont=18,
            bytesPerFrame=15000,packing='row-major; MSB first; 1=white, 0=black'),
            counts=dict(questions=len(course['questions']),exerciseQuestions=sum(bool(q['exercise']) for q in course['questions']),
                sourcePages=len(course['sourcePages']),screens=len(course['screens'])),
            coreScreenCounts=[len(l['core']) for l in course['lessons']])
        # Layout errors abort the build in the renderer; successful pages have no
        # truncation. Source tiles record their overlap and full coverage geometry.
        atomic_json(directory/'demo.json',course)
        return course


def get_demo(demo_id):
    if not re.fullmatch(r'[a-f0-9]{32}',demo_id):raise ValueError('Invalid demonstration ID.')
    return json.loads((DEMO_DATA/demo_id/'demo.json').read_text(encoding='utf8'))


def list_demos():
    DEMO_DATA.mkdir(exist_ok=True)
    result=[]
    for path in sorted(DEMO_DATA.glob('*/demo.json'),key=lambda p:p.stat().st_mtime,reverse=True):
        c=json.loads(path.read_text(encoding='utf8'))
        result.append(dict(id=c['id'],title=c['source']['title'],book=c['source']['book'],publisher=c['source']['publisher']))
    return result


def demo_asset(demo_id,relative):
    if not re.fullmatch(r'(?:frames/s\d{5}\.(?:png|bin)|evidence/page-\d{4}\.(?:png|txt)|source\.pdf|demo\.json)',relative):
        raise ValueError('Invalid demonstration asset.')
    get_demo(demo_id)
    return DEMO_DATA/demo_id/relative


def export_demo(demo_id):
    c=get_demo(demo_id)
    directory=DEMO_DATA/demo_id
    output=directory/'astar-chapter-one.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for file in [directory/'demo.json',directory/'source.pdf',*sorted((directory/'frames').glob('*')),*sorted((directory/'evidence').glob('*'))]:
            archive.write(file,file.relative_to(directory))
        archive.writestr('README.txt','ASTAR Chapter 1 device package\n400 x 300; 1-bit PNG and 15000-byte raw framebuffers.\nRaw: row-major, MSB first, 1=white.\nSource PDF and exact region/page references in demo.json.\nThis package contains data and frames, not firmware.\n')
    return output
