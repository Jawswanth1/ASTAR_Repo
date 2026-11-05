import copy
import tempfile
import unittest
from pathlib import Path
import pymupdf as pdf
from astar_app.converter import convert_pdf
from astar_app.storage import validate_course,portable_course,install_portable,atomic_json
from astar_app.structure import evidence_hash,reconstruct

class StructureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'test-results');self.root=Path(self.temp.name)
        self.source=self.root/'book.pdf';doc=pdf.open()
        p=doc.new_page();p.insert_text((60,60),'Chapter 1: Test',fontsize=20)
        p.insert_text((60,110),'1.1 Reading',fontsize=16)
        p.insert_text((60,150),'This original fixture describes shapes and keeps every source word.',fontsize=12)
        p.insert_text((60,210),'Exercise 1.1',fontsize=16)
        p.insert_text((60,250),'1. Which of these is a triangle? Choose the correct option.',fontsize=12)
        p.insert_text((60,275),'(a) Three sides   (b) Four sides',fontsize=12)
        p.insert_text((60,310),'2. Observe the figure. Explain your answer.',fontsize=12)
        p.insert_text((60,340),'(i) Count the sides.   (ii) Name the shape.',fontsize=12)
        p.draw_polyline([(100,390),(150,450),(50,450)],closePath=True)
        p=doc.new_page();p.insert_text((60,60),'Answers',fontsize=20)
        p.insert_text((60,170),'Exercise 1.1',fontsize=16)
        p.insert_text((60,210),'1. (a)',fontsize=12)
        p.insert_text((60,250),'2. A triangle.',fontsize=12)
        doc.save(self.source);doc.close()
        self.directory=self.root/('a'*32)
        self.course=convert_pdf(self.source,self.directory,dict(ocr=False,minLessons=1,wordsPerLesson=500))

    def tearDown(self):self.temp.cleanup()

    def test_questions_options_answers_and_raw_evidence_survive_export(self):
        c=self.course;validate_course(c);m=c['structure'];objects=m['objects']
        self.assertEqual(len([o for o in objects if o['kind']=='question']),2)
        self.assertEqual(len([o for o in objects if o['kind']=='option']),2)
        self.assertEqual(len([o for o in objects if o['kind']=='subquestion']),2)
        answers=[o for o in objects if o['kind']=='answer'];self.assertEqual(len(answers),2)
        self.assertTrue(all(any(l['kind']=='answer-candidate' and l['status']=='unverified' for l in o['links']) for o in answers))
        self.assertTrue(all(not l['questions'] for l in c['lessons']))
        atomic_json(self.directory/'course.json',c)
        package=portable_course(self.directory)
        self.assertIn('assets/original-0002.png',package['assets'])
        (self.root/'imports').mkdir()
        installed=install_portable(package,self.root/'imports')
        self.assertEqual(installed['structure']['evidenceHash'],m['evidenceHash'])

    def test_rejects_corruption_and_dangling_relationships(self):
        for mutation in ['text','span','hash','link','cycle']:
            c=copy.deepcopy(self.course);m=c['structure'];obj=m['objects'][0]
            if mutation=='text':obj['text']='Invented content'
            elif mutation=='span':obj['source'][0]['page']=999
            elif mutation=='hash':m['evidence']['pages'][0]['blocks'][0]['text']='Changed evidence'
            elif mutation=='link':obj['links']=[dict(targetId='obj-999999',status='checked')]
            else:obj['parentId']=obj['id']
            with self.assertRaises(ValueError,msg=mutation):validate_course(c)

    def test_review_correction_keeps_original(self):
        obj=self.course['structure']['objects'][0];original=obj['text']
        obj.update(correction='Reviewer transcription');obj['review']=dict(status='needs-correction',note='Compare with source.')
        validate_course(self.course)
        self.assertEqual(obj['text'],original)

    def test_json_numeric_roundtrip_does_not_change_evidence_hash(self):
        self.assertEqual(evidence_hash({'width':595.0,'bounds':[0.0,10.5]}),evidence_hash({'width':595,'bounds':[0,10.5]}))

    def test_formula_tokens_are_not_answers_and_syllabus_ends_answer_section(self):
        def page(n,contents,excluded=False):
            blocks=[dict(id=f'p{n}-b{i}',text=text,bbox=[60,60+i*100,500,90+i*100],mathLayout=math) for i,(text,math) in enumerate(contents)]
            return dict(number=n,width=600,height=800,image=f'assets/page-{n:04d}.png',source='text',blocks=blocks,
                disposition='excluded' if excluded else 'learning',excludedReason='Reference matter: Answers' if excluded else None)
        raw=[page(1,[('Exercise 1.1',False),('1. Find the first number.',False),('5. Find the fifth number.',False)]),
             page(2,[('Answers',False),('Exercise 1.1',False),('1. 10',False),('5. A fraction\n1)(2 )\n1)\n2',True)],True),
             page(3,[('SYLLABUS',False),('Number systems and geometry.',False)],True)]
        analyzed=copy.deepcopy(raw)
        for p in analyzed[1:]:p['blocks']=[]
        model=reconstruct(raw,analyzed,[dict(id='ch-1',startPage=1,title='Chapter 1')])
        answers=[o for o in model['objects'] if o['kind']=='answer']
        self.assertEqual([o['label'] for o in answers],['1','5'])
        self.assertTrue(all(r['page']==2 for o in answers for r in o['source']))
        self.assertIn('1)(2 )',answers[-1]['text'])

if __name__=='__main__':unittest.main()
