import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf as pdf
from astar_app import learn


class ChapterLearningTests(unittest.TestCase):
    def test_uploaded_chapter_is_complete_and_chapter_two_excluded(self):
        with tempfile.TemporaryDirectory(dir=learn.ROOT/'test-results') as temporary, patch.object(learn,'DATA',Path(temporary)):
            book_id='a'*32;folder=learn.directory(book_id);folder.mkdir()
            document=pdf.open()
            for text in ['Front matter', 'Chapter 1\n1. Which value equals two plus two?\n(a) 3\n(b) 4\n(c) 5\nAnswer: b\nAll this first-page text must survive.',
                         'The final paragraph of chapter one must survive.\n2. Why is addition useful? Explain with an example.',
                         'CHAPTER TWO MUST NEVER APPEAR']:
                page=document.new_page();page.insert_text((50,80),text)
            document.set_toc([[1,'Chapter 1',2],[1,'Chapter 2',4]]);document.save(folder/'source.pdf');document.close()
            info=learn.inspect(book_id,'fixture.pdf');self.assertEqual((info['first'],info['last']),(2,3))
            course=learn.build(book_id)
            self.assertEqual([p['number'] for p in course['pages']],[2,3])
            self.assertIn('final paragraph',course['pages'][-1]['text'])
            self.assertNotIn('CHAPTER TWO',json.dumps(course))
            self.assertEqual([n for l in course['lessons'] for n in l['pages']],[2,3])
            question=next(q for q in course['questions'] if q['kind']=='mcq')
            self.assertEqual(question['choices'],['3','4','5']);self.assertEqual(question['answer'],1)
            self.assertTrue(all(p['blocks'] for p in course['pages']))
            self.assertTrue(all('image' not in p for p in course['pages']))

    def test_unreadable_pdf_fails_without_requesting_page_numbers(self):
        with tempfile.TemporaryDirectory(dir=learn.ROOT/'test-results') as temporary, patch.object(learn,'DATA',Path(temporary)):
            book_id='b'*32;folder=learn.directory(book_id);folder.mkdir();document=pdf.open();document.new_page();document.save(folder/'source.pdf');document.close()
            with self.assertRaisesRegex(ValueError,'automatically'):learn.inspect(book_id)

    def test_automatic_scope_excludes_solution_bookmarks(self):
        from astar_app.learn_text import automatic_scope
        document=pdf.open()
        page=document.new_page();page.insert_text((50,80),'A SQUARE AND A CUBE\n'+('This chapter explains squares and cubes. '*8))
        document.new_page();document.new_page()
        document.set_toc([[1,'Chapter-1 Solution',3]])
        first,last,chapters=automatic_scope(document)
        self.assertEqual((first,last),(1,2));self.assertEqual(chapters[0]['number'],1)

    def test_superscripts_remain_selectable_text(self):
        from astar_app.learn_text import extract_blocks
        with tempfile.TemporaryDirectory(dir=learn.ROOT/'test-results') as temporary:
            d=pdf.open();p=d.new_page();p.insert_text((50,100),'5',fontsize=12);p.insert_text((57,95),'2',fontsize=7)
            blocks=extract_blocks(p,1,Path(temporary))
            self.assertTrue(any('<sup>2</sup>' in b['html'] for b in blocks))

    def test_ganita_mcq_answer_bank(self):
        from astar_app.learn_mcqs import ganita_mcqs
        bank=ganita_mcqs();self.assertGreaterEqual(len(bank),60)
        self.assertEqual(len({q['id'] for q in bank}),len(bank))
        self.assertTrue(all(0<=q['answer']<len(q['choices']) for q in bank))
        for q in bank:
            match=__import__('re').search(r'table: (\d+)([²³])',q['prompt'])
            if match:self.assertEqual(int(q['choices'][q['answer']]),int(match[1])**(2 if match[2]=='²' else 3))

    def test_session_budget_coverage_and_question_assignment(self):
        pages=[dict(number=i,words=500,topic='A topic') for i in range(1,7)]
        questions=[dict(id=f'q{i}',page=(i//4)+1,kind='mcq' if i%4==0 else 'long') for i in range(24)]
        lessons=learn.plan_lessons(pages,questions)
        self.assertEqual([n for l in lessons for n in l['pages']],list(range(1,7)))
        self.assertEqual(set(q['id'] for q in questions),{q for l in lessons for q in l['questions']})
        self.assertTrue(all(l['estimatedMinutes']<=30 for l in lessons))
        self.assertTrue(all(l['targetMinutes']==30 for l in lessons))

    def test_asset_path_validation(self):
        for bad in ['../source.pdf','assets/../../source.pdf','assets/a.png/../source.pdf']:
            with self.assertRaises(ValueError):learn.asset('a'*32,bad)
        with self.assertRaises(ValueError):learn.directory('../outside')


if __name__=='__main__':unittest.main()
