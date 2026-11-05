import tempfile
import unittest
from pathlib import Path
from astar_app.converter import convert_pdf
from astar_app.sessions import session_settings
from astar_app.storage import validate_course
from test_conversion import make_book


class SessionTests(unittest.TestCase):
    def test_sessions_preserve_words_questions_and_unit_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'book.pdf'
            make_book(source, chapters=2, pages_per_chapter=2)
            base = dict(ocr=False, minLessons=1, wordsPerLesson=220)
            old = convert_pdf(source, root/('a'*32), base)
            new = convert_pdf(source, root/('b'*32), dict(base, planningMode='sessions', expectedUnits=3))
            def words(course, chapter):
                return ' '.join(b['text'] for l in course['lessons'] if l['chapterId']==chapter for b in l['blocks']).split()
            for chapter in old['chapters']:
                self.assertEqual(words(old,chapter['id']), words(new,chapter['id']))
            self.assertLessEqual(len(new['lessons']),len(old['lessons']))
            self.assertTrue(all(l['session']['targetMinutes']==30 for l in new['lessons']))
            self.assertTrue(any('UNIT COUNT MISMATCH' in w for w in new['report']['warnings']))
            self.assertIn('Why do plants need sunlight?', ' '.join(b['text'] for l in new['lessons'] for b in l['blocks']))
            self.assertTrue(all(not l['questions'] for l in new['lessons']))
            figures=[b for l in new['lessons'] for b in l['blocks'] if b['type']=='figure']
            self.assertEqual(len(figures),4, 'Each connected drawing should remain one figure per page.')
            validate_course(new)

    def test_invalid_timing_rejected(self):
        for settings in [dict(practiceMinutes=30),dict(readingWpm=0),dict(sessionMinutes=0),dict(expectedUnits=-1),dict(planningMode='guess')]:
            with self.assertRaises(ValueError):session_settings(settings)

if __name__=='__main__':unittest.main()
