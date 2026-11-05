"""Chapter-one learning: source pages first, timed practice, explicit answer keys."""
from __future__ import annotations
import hashlib
import json
import math
import re
from pathlib import Path
import pymupdf as pdf
from . import demo
from .converter import learning_pixmap
from .storage import atomic_json
from .learn_text import GANITA_HASH, automatic_scope, furniture, extract_blocks
from .learn_mcqs import ganita_mcqs

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'learning-data'
VERSION = 2
CHAPTERS = ['Rational Numbers','Linear Equations in One Variable','Construction of Quadrilaterals',
 'Exponents and Powers','Comparing Quantities using Proportion','Square Roots and Cube Roots',
 'Frequency Distribution Tables and Graphs','Exploring Geometrical Figures','Area of Plane Figures',
 'Direct and Inverse Proportions','Algebraic Expressions','Factorisation','Visualizing 3-D in 2-D',
 'Surface Area and Volume','Playing with Numbers']

# Each checkpoint points to the original question region. Choices, explanations,
# hints and worked answers are ASTAR additions, never represented as book quotes.
CHECKPOINTS = [
 (1,270,440,'How much does each pen cost?', ['₹5','₹22/5','₹5/22','₹22'],1,
  'The packet has 5 pens for ₹22. One pen costs 22 ÷ 5 = ₹22/5 = ₹4.40.', 'Divide the price of the packet by the number of pens.'),
 (2,710,746,'Is every natural number, whole number and integer a rational number ?', ['Yes','Only natural numbers','Only positive integers','No'],0,
  'Every integer n can be written as n/1. The denominator is nonzero, so it is rational.', 'Try writing any integer with a denominator of 1.'),
 (5,120,172,'Write multiplicative inverse', ['11','−11','1/11','−1/11'],2,
  'For the listed number 11, the reciprocal is 1/11 because 11 × 1/11 = 1.', 'Answer for 11 in the original list. Find the factor that gives a product of 1.', 'For the number 11 in the original list'),
 (8,510,560,'If we exclude zero from the set of integers then is it closed under division?', ['Yes, always','No','Only negative integers','Only positive integers'],1,
  'No. For example, 1 ÷ 2 = 1/2, which is not an integer. Both inputs are nonzero integers.', 'Try dividing 1 by 2.'),
 (11,380,508,None,['Yes: the two quotients are equal','No: the two quotients are different'],1,
  'The left quotient is (7/3) ÷ (14/9) = 3/2. Reversing the order gives 2/3. They are different.', 'Compute each side by multiplying by the reciprocal.', 'Does the equality in the original division question hold?'),
 (14,256,528,None,['Yes, subtraction is associative','No, subtraction is not associative'],1,
  'Changing the brackets can change a subtraction result. For example, (1 − 2) − 3 = −4, but 1 − (2 − 3) = 2.', 'Keep the numbers and their order fixed. Change only the grouping.', 'Do the subtraction calculations support associativity?'),
 (16,537,560,'Does the set of natural numbers have additive identity ?', ['Yes: 1','Yes: −1','No, because 0 is not in this book’s natural-number set','Yes: every natural number'],2,
  'An additive identity must be 0. This textbook defines the natural numbers as 1, 2, 3, …, so 0 is not in that set.', 'Which number leaves a value unchanged when added? Is it in the set used here?'),
 (18,524,544,'Write the numbers whose multiplicative inverses are the numbers themselves',['0 and 1','1 and −1','2 and −2','Only 0'],1,
  '1 × 1 = 1 and (−1) × (−1) = 1. Thus 1 and −1 are their own reciprocals.', 'Look for numbers whose square equals 1.'),
 (23,378,422,None,['−7/8','7/8','−17/8','17/8'],0,
  'Let the missing number be x. Then x = −3/2 − (−5/8) = −12/8 + 5/8 = −7/8.', 'Write −5/8 + x = −3/2, then isolate x.', 'Exercise 1.1 · Question 9'),
 (26,145,231,'Are there any natural numbers between 1 and 2?', ['Yes: 3/2','Yes: 0','No','Infinitely many natural numbers'],2,
  'There is no natural number strictly between the consecutive natural numbers 1 and 2. 3/2 is rational but is not natural.', 'Distinguish natural numbers from rational numbers.'),
 (28,469,531,None,['1/2','17/24','4/5','1'],1,
  '2/3 = 16/24 and 3/4 = 18/24, so 17/24 lies strictly between them.', 'Use the textbook hint: rewrite both numbers with a common denominator.', 'Exercise 1.2 · Question 5'),
 (31,514,567,None,['1','2','3','4'],2,
  'The recurring block has three digits, so the periodicity is 3. For example, after the prefix 23, the block 143 repeats.', 'Count the digits in one complete recurring block.', 'First decimal: choose its periodicity'),
 (35,627,671,None,['16/9 m','9/16 m','28 m','64 m'],0,
  'Cloth for one trouser is 64 ÷ 36 = 16/9 metres.', 'Divide the total cloth length by the number of equal-sized trousers.', 'Exercise 1.3 · Question 10'),
]
HINTS = [
 ['Identify the given numbers and the operation the question asks for.','For addition or subtraction, use a common denominator. For division, multiply by the reciprocal of the nonzero divisor.','Show the sign, calculation and simplified result. Substitute back to check it.'],
 ['Name the property being tested: closure, commutativity or associativity.','Calculate both sides with the same inputs. A single counterexample can disprove an “always” claim.','State whether the results agree and explain what that means for the property.'],
 ['Decide whether the target is 0 (additive identity) or 1 (multiplicative identity).','For an additive inverse change the sign; for a nonzero reciprocal swap numerator and denominator.','Verify your answer by carrying out the original operation.'],
 ['Mark the endpoints or rewrite them with a common denominator.','Divide each unit into equal parts. To find an intermediate number, try the mean of the endpoints.','Check every proposed value against both bounds; keep strict inequalities strict.'],
 ['Decide whether the decimal terminates or has a recurring block.','For a terminating decimal use a power of 10. For a recurring decimal, align the repeated digits before subtracting.','Simplify the fraction and check by dividing. Keep recurring bars visible in the source.'],
]

def directory(book_id):
    if not re.fullmatch(r'[a-f0-9]{32}',book_id): raise ValueError('Invalid book ID.')
    return DATA/book_id

def inspect(book_id, filename='Textbook.pdf'):
    folder=directory(book_id); source=folder/'source.pdf'
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    with pdf.open(source) as doc:
        if doc.needs_pass: raise ValueError('This PDF is locked. Upload an unlocked copy.')
        if not 1 <= len(doc) <= 2000: raise ValueError('Use a PDF with 1–2,000 pages.')
        known=digest==demo.SCERT_HASH
        ganita=digest==GANITA_HASH
        chapters=[]; first=last=None
        if known:
            first,last=13,48;chapters=[dict(number=i+1,title=t) for i,t in enumerate(CHAPTERS)]
        else:
            first,last,chapters=automatic_scope(doc)
            if ganita:chapters=[dict(number=1,title='A Square and a Cube')]
        result=dict(id=book_id,filename=filename,title='Mathematics · Class VIII' if known else 'Ganita Prakash · Grade 8' if ganita else Path(filename).stem,
                    sha256=digest,known=known,ganita=ganita,pdfPages=len(doc),first=first,last=last,chapters=chapters,needsBounds=False)
        atomic_json(folder/'upload.json',result)
        return result

def clean_rect(page,known):
    # The reference book has a verified body boundary. Other books retain the
    # complete page so unknown diagrams or footnotes cannot be silently clipped.
    return pdf.Rect(28,104,page.rect.width-18,750) if known else page.rect

def save_region(page, rect, path):
    pix,_=learning_pixmap(page,1.7)
    from PIL import Image
    image=Image.frombytes('L',(pix.width,pix.height),pix.samples)
    image.crop(tuple(round(v*1.7) for v in rect)).save(path)

def plan_lessons(pages,questions):
    """Pack complete source pages and question attempts into ~30-minute routes."""
    lessons=[];current=None
    def add(kind,item,cost):
        nonlocal current
        if current is None or current['estimatedMinutes']+cost>24:
            current=dict(id=len(lessons)+1,pages=[],questions=[],estimatedMinutes=0,targetMinutes=30)
            lessons.append(current)
        current[kind].append(item);current['estimatedMinutes']+=cost
    for page in pages:
        add('pages',page['number'],max(3,min(15,math.ceil(page['words']/100)+1)))
        for q in [q for q in questions if q['page']==page['number']]:
            add('questions',q['id'],2 if q['kind']=='mcq' else 4)
    for lesson in lessons:
        relevant=[q for q in questions if q['id'] in lesson['questions']]
        if not lesson['pages']:lesson['reviewPages']=sorted({q['page'] for q in relevant})
        else:lesson['reviewPages']=[]
        chapter_pages=lesson['pages'] or lesson['reviewPages']
        lesson['reviewQuestions']=[]
        needed=max(0,3-sum(q['kind']=='mcq' for q in relevant))
        previous=[q for q in questions if q['kind']=='mcq' and q['page']<=max(chapter_pages) and q['id'] not in lesson['questions']]
        for q in previous[-needed:] if needed else []:
            lesson['questions'].insert(0,q['id']);lesson['reviewQuestions'].append(q['id']);lesson['estimatedMinutes']+=2
        topic=next((p['topic'] for p in pages if p['number']==chapter_pages[0]),'Practice')
        lesson['title']=topic if lesson['pages'] else f'{topic} · practice'
        lesson['minutes']=30
        lesson['readingMinutes']=sum(max(3,min(15,math.ceil(p['words']/100)+1)) for p in pages if p['number'] in lesson['pages'])
        lesson['practiceMinutes']=30-lesson['readingMinutes']
    return lessons

def build(book_id,options=None,progress=None):
    options=options or {};progress=progress or (lambda *a:None)
    folder=directory(book_id); previous=json.loads((folder/'upload.json').read_text(encoding='utf8'))
    info=inspect(book_id,previous['filename'])
    first,last=info['first'],info['last']
    if info['known'] and (first,last)!=(13,48): raise ValueError('The reference Chapter 1 is PDF pages 13–48.')
    if not 1<=first<=last<=info['pdfPages'] or last-first>=100:raise ValueError('Chapter 1 could not be identified automatically within the supported chapter length.')
    assets=folder/'assets';assets.mkdir(exist_ok=True)
    questions=[];pages=[]
    with pdf.open(folder/'source.pdf') as doc:
        excluded=furniture(doc,first,last)
        def question(page,rect,label,concept=1,qid=None):
            qid=qid or f'q{len(questions)+1}'; p=doc[page-1]
            q=dict(id=qid,page=page,printedPage=page-12 if info['known'] else None,label=label,kind='long',
                   text=p.get_text(clip=pdf.Rect(rect),sort=True).strip(),
                   hints=HINTS[concept-1],checklist=['I answered every requested part.','I showed the rule or method and my working.','I checked the result against the question.'],
                   origin='Original textbook question',feedbackType='self-check',
                   blocks=extract_blocks(p,page,assets,excluded,clip=pdf.Rect(rect)))
            questions.append(q);return q
        if info['known']:
            for printed,exercise,entries in demo.EXERCISES:
                for n,y0,y1,concept in entries:
                    q=question(printed+12,[78,y0,515,y1],f'Exercise {exercise} · Question {n}',concept,f'ex-{exercise}-{n}')
                    if exercise=='1.1' and n==11:
                        q.update(hints=['Compare (a − b) − c with a − (b − c).','Try a = 1, b = 2, c = 3.','One unequal pair of results disproves associativity.'],
                         modelAnswer='No. (1 − 2) − 3 = −4, whereas 1 − (2 − 3) = 2. Since the results differ, subtraction is not associative.',
                         checklist=['I stated that subtraction is not associative.','I used the same three numbers in both groupings.','I calculated unequal results and explained the conclusion.'])
            for i,(printed,y0,y1,label,concept) in enumerate(demo.EMBEDDED):
                question(printed+12,[30,y0,550,y1],label,concept,f'embedded-{i+1}')
            for n,y0,y1 in [(1,322,361),(2,370,407)]:question(31,[350,y0,584,y1],f'Try these: distributivity ({n})',3,f'distribute-{n}')
            for i,entry in enumerate(CHECKPOINTS):
                printed,y0,y1,prompt,choices,answer,explanation,hint,*target=entry
                q=question(printed+12,[30,y0,550,y1],f'Textbook checkpoint · page {printed}',qid=f'check-{i+1}')
                q.update(kind='mcq',prompt=prompt,target=target[0] if target else None,choices=choices,answer=answer,
                         explanation=explanation,hints=[hint],feedbackType='verified',origin='Textbook prompt · ASTAR answer choices')
        if info.get('ganita'):questions.extend(ganita_mcqs())
        for number in range(first,last+1):
            p=doc[number-1]
            if p.rect.width*p.rect.height>2_000_000:raise ValueError('A PDF page is too large to process safely.')
            rect=clean_rect(p,info['known']);text=p.get_text(clip=rect,sort=True)
            printed=number-12 if info['known'] else number
            topic=next((x['short'] for x in reversed(demo.PLAN) if printed>=x['start'][0]),'Rational numbers') if info['known'] else ('The locker puzzle' if number<=2 else 'Square numbers' if number<=7 else 'Square roots' if number<=10 else 'Cubes and cube roots' if number<=15 else 'History and chapter practice') if info.get('ganita') else 'Chapter 1'
            blocks=extract_blocks(p,number,assets,excluded,clip=rect if info['known'] else None)
            if not any(b['text'].strip() for b in blocks):
                raise ValueError('A chapter page has no extractable text. This version requires a text-based PDF; it will not substitute a page screenshot for a lesson.')
            pages.append(dict(number=number,printedPage=printed if info['known'] else None,
                              text=text,words=len(text.split()),topic=topic,bbox=list(rect),blocks=blocks))
            if not info['known']:
                for b in p.get_text('blocks'):
                    text=b[4].strip()
                    if len(text)<20 or not ('?' in text or re.match(r'^\d+[.)]\s+[A-Za-z]',text)):continue
                    q=question(number,b[:4],'Textbook question')
                    # Grade only an explicit answer attached to this very prompt.
                    options_found=list(re.finditer(r'(?:\(([a-dA-D])\)|\b([a-dA-D])[.)])\s+',text))
                    if len(options_found)>=2:
                        answer_match=re.search(r'\b(?:Answer|Ans)\s*[:.-]\s*\(?([a-d])\)?',text,re.I)
                        end=answer_match.start() if answer_match else len(text)
                        choices=[text[m.end():options_found[j+1].start() if j+1<len(options_found) else end].strip() for j,m in enumerate(options_found)]
                        if all(choices):
                            labels=[(m[1] or m[2]).lower() for m in options_found]
                            q.update(kind='mcq',prompt=text[:options_found[0].start()],choices=choices,
                                     answer=labels.index(answer_match[1].lower()) if answer_match and answer_match[1].lower() in labels else None,
                                     explanation='Compare the explicit answer printed with this textbook question.' if answer_match else None,
                                     feedbackType='textbook-key' if answer_match else 'unverified',origin='Original textbook question and choices')
                    q['hints']=['Identify what the question asks and the information it gives.','Return to the definition or worked example on the source page.','Show each step and check that your conclusion answers the question.']
                    if info.get('ganita'):
                        if 'locker' in text.lower() or number<=2:
                            q['hints']=['Each positive factor corresponds to one person toggling the locker.','Pair each factor d with n ÷ d. A square has a factor that pairs with itself.','An odd number of toggles leaves a locker open. Explain why the square-numbered lockers have this property.']
                        elif number<=10:
                            q['hints']=['Identify the square or square-root relationship in the question.','Try pairing equal prime factors, or locate the number between two familiar squares.','Check your calculation by squaring the proposed root and explain your conclusion.']
                        elif number==18:
                            q['hints']=['List the square totals that two numbers in the given range could make.','Join two numbers when their sum is a square. Look for numbers with very few possible neighbours.','Build a path (or circle) using every number exactly once, and check each adjacent sum.']
                        else:
                            q['hints']=['Write the number as a product of prime factors.','For a cube, equal prime factors must form groups of three.','Multiply one factor from each group to find the cube root, then cube it to check.']
            progress(number-first+1,last-first+1,f'Preparing chapter page {number-first+1} of {last-first+1}')
    # Stable source order; checkpoints accompany the source reading.
    questions.sort(key=lambda q:(q['page'],0 if q['kind']=='mcq' else 1))
    course=dict(id=book_id,version=VERSION,title=info['title'],chapterTitle='Rational Numbers' if info['known'] else 'A Square and a Cube' if info.get('ganita') else 'Chapter 1',
                chapters=info['chapters'],source={**info,'first':first,'last':last},pages=pages,questions=questions,
                lessons=plan_lessons(pages,questions),timingNote='30-minute study targets. Read at your own pace; carry unfinished practice into your next sitting.',
                fidelity='Extracted chapter text, native superscripts and selectable mathematical text. Only actual illustrations use image assets.',
                practiceNote='Choices and hints marked ASTAR are learning aids. Written answers use self-check guidance, not automatic correctness grading.')
    atomic_json(folder/'course.json',course);return course

def get(book_id):
    course=json.loads((directory(book_id)/'course.json').read_text(encoding='utf8'))
    if course.get('version',1)<VERSION:return build(book_id)
    return course

def asset(book_id,relative):
    if not re.fullmatch(r'(?:assets/[a-zA-Z0-9.-]+\.png|source\.pdf)',relative):raise ValueError('Invalid learning asset.')
    return directory(book_id)/relative
