"""Realistic, adversarial textbook layouts with separately checked expectations."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf as pdf
from astar_app.converter import convert_pdf
from astar_app.storage import validate_course

BODY = ('Leaves capture sunlight and make food for the plant. Water travels from the roots through the stem. '
        'The leaf contains cells that carry out photosynthesis. Observe the leaf diagram and compare its parts. ')
LEFT = 'LEFT COLUMN START. ' + BODY*3 + ' LEFT COLUMN END.'
RIGHT = 'RIGHT COLUMN START. ' + BODY*3 + ' RIGHT COLUMN END.'


def make_layout_book(path):
    d=pdf.open()
    p=d.new_page(width=600,height=800)
    p.insert_text((65,160),'Science for curious learners',fontsize=26)
    p.insert_text((65,210),'Class Eight',fontsize=16)
    p.insert_text((65,690),'ISBN 978-0-12345-678-9',fontsize=9)
    p=d.new_page(width=600,height=800)
    p.insert_text((65,80),'Copyright',fontsize=20)
    p.insert_text((65,140),'All rights reserved. Published by Example Press.',fontsize=11)
    p=d.new_page(width=600,height=800)
    p.insert_text((65,80),'Contents',fontsize=20)
    p.insert_text((65,140),'Chapter 1: Plants ............... 5\nChapter 2: Light ............... 7\nReferences ..................... 9',fontsize=11)
    p=d.new_page(width=600,height=800)
    p.insert_text((65,80),'Foreword',fontsize=20)
    p.insert_textbox(pdf.Rect(65,130,535,650),('This publication was prepared by the committee for schools and teachers. '*12),fontsize=11)
    for i in range(2):
        p=d.new_page(width=600,height=800)
        p.insert_text((65,22),'SCIENCE FOR CURIOUS LEARNERS',fontsize=8)
        if i==0:p.insert_text((65,70),'Chapter 1: Plants',fontsize=20)
        p.insert_text((65,105),'1.1 Leaves and sunlight',fontsize=15)
        p.insert_textbox(pdf.Rect(65,140,390,475),BODY*4,fontsize=11)
        p.insert_textbox(pdf.Rect(430,145,575,230),'Scan this QR code\nDownload our app\nSubscribe for new editions',fontsize=9)
        p.insert_textbox(pdf.Rect(430,300,575,420),'Remember\nLeaves capture sunlight. Cells in leaves make food for the plant.',fontsize=10)
        if i==0:
            p.draw_circle((175,545),30)
            p.draw_line((175,575),(175,625))
            p.insert_text((220,550),'Leaf',fontsize=10)
            p.insert_text((65,660),'Figure 1. A leaf receives sunlight.',fontsize=10)
        else:
            p.insert_textbox(pdf.Rect(430,500,575,600),'Old legends describe hidden treasures beneath distant castles.',fontsize=9)
        p.insert_text((65,700),'1. Why do plants need sunlight? Explain in your notebook.',fontsize=11)
        p.insert_text((65,775),str(i+5),fontsize=8)
    p=d.new_page(width=600,height=800)
    p.insert_text((65,22),'SCIENCE FOR CURIOUS LEARNERS',fontsize=8)
    p.insert_text((50,70),'Chapter 2: Light',fontsize=20)
    p.insert_textbox(pdf.Rect(50,120,285,700),LEFT,fontsize=11)
    p.insert_textbox(pdf.Rect(320,120,555,700),RIGHT,fontsize=11)
    p.insert_text((65,775),'7',fontsize=8)
    original=pdf.open();p=original.new_page(width=600,height=800)
    p.insert_text((65,100),'Leaves and water',fontsize=22)
    p.insert_textbox(pdf.Rect(65,150,535,650),BODY*4,fontsize=12)
    scan=p.get_pixmap(dpi=100).tobytes('png')
    p=d.new_page(width=600,height=800);p.insert_image(p.rect,stream=scan);original.close()
    p=d.new_page(width=600,height=800)
    p.insert_text((65,80),'References',fontsize=20)
    p.insert_text((65,140),'Example Press. A guide to plants. Publication information.',fontsize=11)
    d.set_toc([[1,'Cover',1],[1,'Copyright',2],[1,'Contents',3],[1,'Foreword',4],
               [1,'Chapter 1: Plants',5],[1,'Chapter 2: Light',7],[1,'References',9]])
    d.save(path);d.close()


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parent.parent/'test-results';root.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=root)
        self.path=Path(self.temp.name);make_layout_book(self.path/'layout.pdf')
        with patch('astar_app.converter.ocr_available',return_value=False):
            self.course=convert_pdf(self.path/'layout.pdf',self.path/('b'*32),
                                    {'title':'Layout challenge','subject':'Science','minLessons':1,'wordsPerLesson':200})
        validate_course(self.course)

    def tearDown(self):self.temp.cleanup()

    def text(self):return ' '.join(b['text'] for l in self.course['lessons'] for b in l['blocks'])

    def test_front_matter_and_references_do_not_become_lessons(self):
        self.assertEqual({p['number'] for p in self.course['report']['pages'] if p['disposition']=='excluded'},{1,2,3,4,9})
        self.assertEqual(self.course['lessons'][0]['pageStart'],5)
        self.assertEqual(len(self.course['chapters']),2)
        self.assertTrue(all(b['page'] not in {1,2,3,4,9} for l in self.course['lessons'] for b in l['blocks']))

    def test_filters_furniture_and_promotion_but_keeps_learning_callouts(self):
        content=self.text()
        for unwanted in ['ISBN','All rights reserved','Subscribe','Download our app','SCIENCE FOR CURIOUS LEARNERS']:
            self.assertNotIn(unwanted,content)
        self.assertIn('Remember',content)
        self.assertIn('Figure 1. A leaf receives sunlight.',content)
        self.assertIn('Why do plants need sunlight?',content)
        exclusions=self.course['report']['analysis']['excluded']
        self.assertTrue(any('Subscribe' in e['text'] and e['reason'] for e in exclusions))
        self.assertTrue(all(not e['restored'] for e in exclusions))

    def test_preserves_main_text_without_summarizing(self):
        blocks=[b['text'] for l in self.course['lessons'] for b in l['blocks'] if b['page']==5]
        self.assertIn(' '.join((BODY*4).split()),' '.join(' '.join(blocks).split()))

    def test_reads_two_columns_in_order_not_interleaved(self):
        content=' '.join(b['text'] for l in self.course['lessons'] for b in l['blocks'] if b['page']==7)
        self.assertLess(content.index('LEFT COLUMN END'),content.index('RIGHT COLUMN START'))
        self.assertEqual(self.course['report']['pages'][6]['columnOrder'],'left column, then right column')

    def test_ambiguous_margin_is_preserved_and_flagged(self):
        self.assertIn('Old legends describe hidden treasures',' '.join(self.text().split()))
        self.assertTrue(any(i['code']=='ambiguous_margin' for l in self.course['lessons'] for i in l['quality']['issues']))

    def test_triage_prioritizes_actual_ocr_failure_over_uncertain_margin(self):
        q=self.course['report']['quality']
        ordered=[next(l for l in self.course['lessons'] if l['id']==i) for i in q['queue']]
        self.assertEqual(ordered[0]['quality']['severity'],'high')
        self.assertEqual(ordered[0]['pageStart'],8)
        self.assertGreater(q['automatic'],0)
        self.assertLess(q['attention'],len(self.course['lessons']))
        normal=[l for l in self.course['lessons'] if l['pageStart']==5 and l['pageEnd']==5]
        self.assertTrue(normal)
        self.assertTrue(all(l['quality']['status']=='auto' for l in normal))

    def test_diagrams_are_extracted_into_the_learning_stream(self):
        figures=[b for l in self.course['lessons'] for b in l['blocks'] if b['type']=='figure']
        self.assertTrue(figures)
        self.assertTrue(all((self.path/('b'*32)/b['image']).exists() for b in figures))

    def test_human_review_resolves_queue_without_marking_every_lesson(self):
        c=copy.deepcopy(self.course)
        first=c['report']['quality']['queue'][0]
        lesson=next(l for l in c['lessons'] if l['id']==first);lesson['reviewed']=True
        validate_course(c)
        self.assertNotIn(first,c['report']['quality']['queue'])
        self.assertTrue(any(not l['reviewed'] and l['quality']['status']=='auto' for l in c['lessons']))

    def test_filename_bookmarks_skip_preliminary_continuations(self):
        path=self.path/'filename.pdf';d=pdf.open()
        for i in range(3):
            p=d.new_page();p.insert_text((60,80),'Preface' if i==0 else 'Committee introduction',fontsize=18)
            p.insert_textbox(pdf.Rect(60,140,500,700),'This book was developed by an educational committee. '*20,fontsize=11)
        p=d.new_page();p.insert_text((60,80),'Chapter',fontsize=18);p.insert_text((400,80),'1',fontsize=30)
        p.insert_text((60,130),'Leaves and water',fontsize=22);p.insert_textbox(pdf.Rect(60,180,500,700),BODY*4,fontsize=11)
        d.set_toc([[1,'0.pdf',1],[1,'Ch_01_Leaves.pdf',4]]);d.save(path);d.close()
        c=convert_pdf(path,self.path/('c'*32),{'minLessons':1,'wordsPerLesson':200})
        self.assertEqual(c['lessons'][0]['pageStart'],4)
        self.assertEqual(c['chapters'][0]['title'],'Leaves and water')

    def test_stacked_maths_uses_complete_learning_crop(self):
        path=self.path/'maths.pdf';d=pdf.open();p=d.new_page()
        p.insert_text((60,70),'Chapter 1: Fractions',fontsize=20)
        p.insert_text((60,130),'Fractions can be added using a common denominator.',fontsize=12)
        p.insert_text((80,190),'1\n2\n+\n3\n4\n=\nx',fontsize=12)
        p.insert_text((300,190),'a\nb\n-\nc\nd\n=\ny',fontsize=12)
        p.draw_line((75,202),(95,202));p.draw_line((295,202),(315,202))
        d.save(path);d.close()
        c=convert_pdf(path,self.path/('d'*32),{'minLessons':1,'wordsPerLesson':80})
        validate_course(c)
        self.assertEqual(len(c['lessons']),1)
        lesson=c['lessons'][0];self.assertEqual(lesson['presentation'],'layout')
        self.assertTrue((self.path/('d'*32)/lesson['panels'][0]['focusImage']).exists())
        self.assertEqual(lesson['quality']['status'],'auto')


if __name__=='__main__':unittest.main()
