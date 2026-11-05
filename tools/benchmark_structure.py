"""Run the complete representative book; score only declared reviewed samples."""
from pathlib import Path
import sys,json,hashlib,shutil,re
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from astar_app.converter import convert_pdf
from astar_app.storage import atomic_json,validate_course

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'benchmarks/representative-book'
BOOK=ROOT/'8 maths em 2020-21.pdf'
COURSE=OUT/'11111111111111111111111111111111'
def run():
    COURSE.mkdir(parents=True,exist_ok=True)
    shutil.copy2(BOOK,COURSE/'source.pdf')
    def progress(n,total,message):
        if n%50==0 or n==total:print(f'{n}/{total} {message}',flush=True)
    c=convert_pdf(COURSE/'source.pdf',COURSE,dict(title='Class VIII Mathematics — structural review',planningMode='sessions',expectedUnits=15,ocr=False),progress)
    atomic_json(OUT/'candidate.json',c)
    validate_course(c);atomic_json(COURSE/'course.json',c)
    evaluate(c)

def evaluate(c):
    m=c['structure'];objects=m['objects']
    def onpage(o,p):return any(r['page']==p for r in o['source'])
    def normalized(t):return ' '.join(t.split())
    # These assertions were transcribed from rendered source pages, independently
    # of the new structural model. They are a targeted diagnostic set, not a
    # representative statistical sample of all 374 pages.
    q_expected={
      '1':'Find the sum of integers which are divisible by 5 from 1 to 100.',
      '2':'Find the sum of integers which are divisible by 2 from 11 to 50.',
      '3':'Find the sum of integers which are divisible by 2 and 3 from 1 to 50.',
      '7':'Find the number of rectangles of the given figure ?',
      '9':'Find the sum of integers from 1 to 100 which are divisible by 2 or 5.',
      '10':'Find the sum of integers from 11 to 1000 which are divisible by 3.'}
    qs=[o for o in objects if o['kind']=='question' and o.get('exercise')=='15.6' and onpage(o,351)]
    by_number={o['label']:o for o in qs}
    checked=sum(normalized(t)==normalized(re.sub(r'^\s*\d+[.)]\s*','',by_number.get(k,{}).get('text',''))) for k,t in q_expected.items())
    paragraphs=['Four times a number reduced by 5 equals 19. Find the number.',
      'Hence the required number is 6',
      'The length of a rectangle shaped park exceeds its breadth by 17 meters. If the perimeter of the park is 178 meters find the dimensions of the park?']
    atomic_json(OUT/'gold-sample.json',dict(sourceSHA256=hashlib.sha256(BOOK.read_bytes()).hexdigest(),
        annotationMethod='Transcribed/checked against rendered original PDF pages during this task; targeted diagnostic sample, not exhaustive human ground truth.',
        questions=dict(page=351,exercise='15.6',expectedNumbers=list(range(1,11)),prosePrompts=q_expected),
        prose=dict(page=54,spans=paragraphs),subparts=dict(page=57,exercise='2.2',question='1',markers=['(i)','(ii)','(iii)','(iv)','(v)']),
        answers=dict(page=367,exercise='15.6',expectedNumbers=list(range(1,11))),
        unannotated=['full-book mathematical fidelity','full-book reading order','MCQ option completeness','table cells','precise diagram associations']))
    page_text=normalized(' '.join(o['text'] for o in objects if onpage(o,54)))
    sub=[o for o in objects if o['kind']=='subquestion' and o.get('exercise')=='2.2' and onpage(o,57)]
    labels=[o['label'] for o in sub]
    answers=[o for o in objects if o['kind']=='answer' and o.get('exercise')=='15.6' and onpage(o,367)]
    def metric(passed,total,meaning):
        assert 0<=passed<=total, (passed,total,meaning)
        return dict(passed=passed,total=total,percent=round(100*passed/total,1) if total else None,meaning=meaning)
    metrics={
      'paragraph_text_presence':metric(sum(normalized(t) in page_text for t in paragraphs),3,'Three reviewed prose spans on page 54; not paragraph segmentation or mathematical fidelity.'),
      'question_text_exact_match':metric(checked,6,'Exact normalized prose and boundary match for six reviewed prompts from exercise 15.6, page 351. Superscript-bearing questions excluded.'),
      'question_numbering':metric(sum(str(i) in by_number for i in range(1,11)),10,'Expected numbers 1–10 on page 351. Extra detections recorded separately.'),
      'subquestion_marker_recall':metric(sum(x in labels for x in ['(i)','(ii)','(iii)','(iv)','(v)']),5,'Markers under exercise 2.2 question 1, page 57. Does not certify complete diagram-to-subpart association.'),
      'verified_diagram_associations':metric(0,1,'Question 15.6/7 has a diagram on page 351. No correct association has been independently verified; this is an unmet review gate, not a measured diagram-recall rate.'),
      'answer_option_completeness':metric(0,0,'No independently annotated MCQ in this diagnostic sample; not measured.'),
      'page_reference_accuracy':metric(sum(onpage(by_number.get(str(i),{'source':[]}),351) for i in range(1,11)),10,'Physical PDF page references of the ten sampled questions.'),
      'question_reading_order':metric(int([o['label'] for o in qs]==[str(i) for i in range(1,11)]),1,'Question-number sequence on page 351, not full-book visual reading order.'),
      'structural_reconstruction':metric(sum(any(o['kind']==kind and o['label']==label and onpage(o,p) for o in objects) for kind,label,p in [('section','2.3.1',53),('example','5',54),('example','6',54),('exercise','15.6',351)]),4,'Four sampled section/example/exercise boundaries.'),
      'answer_candidate_mapping':metric(sum(len([a for a in answers if a['label']==str(n)])==1 and any(l['kind']=='answer-candidate' and l['targetId']==by_number.get(str(n),{}).get('id') for a in answers if a['label']==str(n) for l in a['links']) for n in range(1,11)),10,'Unique number-based candidate mappings to ten source answer entries; duplicates fail the check. All mappings remain unverified and unusable for automatic grading.')}
    summary=dict(sourceSHA256=hashlib.sha256(BOOK.read_bytes()).hexdigest(),pages=c['source']['pages'],units=len(c['chapters']),sessions=len(c['lessons']),
        detectedTypes=m['coverage']['types'],samplePages=[53,54,57,351,367],metrics=metrics,
        sampleQuestionDetections=len(qs),sampleAnswerDetections=len(answers),sampleSubquestionLabels=labels,
        releaseGate='NOT READY for unattended educational publication. Sample metrics do not establish full-book accuracy.',
        limitations=['Selected diagnostic pages, not a randomized or exhaustive gold corpus.','Raw source preservation is not semantic extraction accuracy.','Mathematics, table cells, graphical subparts and whole-book reading order still require independent annotation.','No benchmark score is based on a generated answer key.'])
    atomic_json(OUT/'results.json',summary)
    lines=['# Extraction benchmark — representative textbook','',summary['releaseGate'],'',f"Full run: {summary['pages']} pages, {summary['units']} units, {summary['sessions']} sessions.",'','## Reviewed diagnostic sample','', '| Metric | Passed / checked | Percent | Meaning |','| --- | --- | --- | --- |']
    for name,v in metrics.items():lines.append(f"| {name} | {v['passed']} / {v['total']} | {str(v['percent'])+'%' if v['percent'] is not None else 'Not measured'} | {v['meaning']} |")
    lines+=['','## Limits','']+['- '+s for s in summary['limitations']]
    (OUT/'BENCHMARK_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':
    if '--reconstruct' in sys.argv:
        import copy,pymupdf as pdf
        from astar_app.analysis import analyze_pages
        from astar_app.structure import reconstruct
        c=json.loads((COURSE/'course.json').read_text(encoding='utf-8'));m=c['structure'];raw=[]
        for p in m['evidence']['pages']:
            original=copy.deepcopy(p)
            original.update(source=p['method'],originalImage=p['image'],image=f"assets/page-{p['number']:04d}.png",warnings=[],hasInk=True,
                structureVisuals=[o['source'][0]['bbox'] for o in m['objects'] if o['kind']=='figure' and o['source'][0]['page']==p['number']],
                tables=[dict(bbox=o['source'][0]['bbox'],cells=o.get('cells',[])) for o in m['objects'] if o['kind']=='table' and o['source'][0]['page']==p['number']])
            # Preserve the original decision about which raw blocks were excluded;
            # this replay changes interpretation only, not the extraction layer.
            raw.append(original)
        analyzed=copy.deepcopy(raw)
        excluded={e['id'].removeprefix('excluded-') for e in c['report']['analysis']['excluded']}
        for p,report in zip(analyzed,c['report']['pages']):
            p.update(disposition=report['disposition'],excludedReason=report.get('excludedReason'))
            p['blocks']=[b for b in p['blocks'] if b['id'] not in excluded]
        c['structure']=reconstruct(raw,analyzed,c['chapters']);validate_course(c);atomic_json(COURSE/'course.json',c);evaluate(c)
    elif '--evaluate' in sys.argv:evaluate(json.loads((COURSE/'course.json').read_text(encoding='utf-8')))
    else:run()
