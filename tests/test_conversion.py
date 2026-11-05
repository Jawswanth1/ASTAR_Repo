"""Functional conversion checks using original, locally generated PDF fixtures."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf as pdf
from PIL import Image

from astar_app.converter import convert_pdf, split_text, learning_pixmap
from astar_app.storage import atomic_json, install_portable, portable_course, validate_course
from astar_app.server import render_reader


def make_book(path, chapters=2, pages_per_chapter=2):
    doc = pdf.open()
    toc = []
    expected = []
    for chapter in range(1, chapters+1):
        toc.append([1, f"Chapter {chapter}: Light and life", len(doc)+1])
        for number in range(pages_per_chapter):
            page = doc.new_page(width=500, height=700)
            page.insert_text((35, 40), f"Chapter {chapter}: Light and life", fontsize=16)
            # Original content: enough words to exercise meaningful lesson splits.
            paragraph = ("Plants capture sunlight in their leaves. Water moves through the stem. "
                         "Observe the labelled drawing and record what you see in your notebook. ")
            for block in range(5):
                page.insert_textbox(pdf.Rect(35, 65+block*90, 465, 150+block*90),
                                    f"Section {chapter}.{number+1}.{block+1}\n" + paragraph*2, fontsize=10)
            page.draw_circle((130, 570), 30)
            page.draw_line((130, 600), (130, 645))
            page.insert_text((180, 575), "A leaf receives sunlight.", fontsize=10)
            page.insert_text((35, 675), "1. Why do plants need sunlight? Explain in your notebook.", fontsize=10)
            extracted=page.get_text("text", sort=True)
            # The large repeated chapter title on continuation pages is furniture.
            if number:
                extracted=extracted.replace(f"Chapter {chapter}: Light and life\n",'',1)
            expected.append(extracted)
    doc.set_toc(toc)
    doc.save(path)
    doc.close()
    return expected


class ConversionTests(unittest.TestCase):
    def setUp(self):
        test_root = Path(__file__).resolve().parent.parent / 'test-results'
        test_root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=test_root)
        self.root = Path(self.temp.name)
        self.source = self.root / "book.pdf"
        self.output = self.root / ("a"*32)

    def tearDown(self):
        self.temp.cleanup()

    def convert(self, **kwargs):
        options = {"title":"Original science fixture", "subject":"Science", "language":"eng",
                   "minLessons":8, "wordsPerLesson":180, **kwargs}
        return convert_pdf(self.source, self.output, options)

    def test_text_preservation_diagrams_and_chapters(self):
        expected = make_book(self.source)
        course = self.convert()
        validate_course(course)
        self.assertEqual(len(course["chapters"]), 2)
        # Compare all words in source order, not just a word count.
        actual = " ".join(b["text"] for l in course["lessons"] for b in l["blocks"])
        self.assertEqual(actual.split(), " ".join(expected).split())
        self.assertTrue(any(b["type"] == "question" for l in course["lessons"] for b in l["blocks"]))
        with Image.open(self.output / "assets/page-0001.png") as image:
            self.assertEqual(image.mode, "1")
            self.assertGreater(image.width, 500)
            # Vector drawing must survive rasterization, not only embedded bitmaps.
            self.assertLess(image.crop((130, 860, 280, 1000)).getextrema()[0], 255)

    def test_twenty_chapters_meet_150_without_losing_text(self):
        expected = make_book(self.source, chapters=20, pages_per_chapter=2)
        course = self.convert(minLessons=150)
        validate_course(course)
        self.assertEqual(len(course["chapters"]), 20)
        self.assertGreaterEqual(len(course["lessons"]), 150)
        actual = " ".join(b["text"] for l in course["lessons"] for b in l["blocks"])
        self.assertEqual(actual.split(), " ".join(expected).split())

    def test_small_book_reports_target_shortfall(self):
        doc = pdf.open(); page = doc.new_page(); page.insert_text((50,50),"A short original page about light."); doc.save(self.source); doc.close()
        course = self.convert(minLessons=150)
        self.assertLess(len(course["lessons"]),150)
        self.assertTrue(any("below" in w for w in course["report"]["warnings"]))

    def test_scanned_book_keeps_images_when_ocr_unavailable(self):
        doc = pdf.open(); page = doc.new_page(); page.draw_circle((200,200),60)
        pix = page.get_pixmap(); scan = pdf.open(); p = scan.new_page(); p.insert_image(p.rect,stream=pix.tobytes("png")); scan.save(self.source); scan.close(); doc.close()
        with patch('astar_app.converter.ocr_available',return_value=False):
            course = self.convert()
        validate_course(course)
        self.assertEqual(course["lessons"][0]["blocks"][0]["type"],"source")
        self.assertTrue(course["report"]["pages"][0]["warnings"])
        self.assertTrue((self.output/'assets/page-0001.png').exists())

    def test_manual_chapters_and_invalid_pages(self):
        make_book(self.source)
        course = self.convert(chapterPlan="2 | Cells\n4 | Living things")
        self.assertEqual([c["title"] for c in course["chapters"]],["Cells","Living things"])
        self.assertTrue(all(l['pageStart']>=2 for l in course['lessons']))
        with self.assertRaises(ValueError):self.convert(chapterPlan="99 | Missing page")
        with self.assertRaises(ValueError):self.convert(chapterPlan="2 | A\n2 | B")

    def test_export_import_and_standalone_are_self_contained(self):
        make_book(self.source)
        course=self.convert();atomic_json(self.output/'course.json',course)
        exported=portable_course(self.output)
        root=self.root/'installed';root.mkdir()
        installed=install_portable(copy.deepcopy(exported),root)
        self.assertNotEqual(installed['id'],course['id'])
        validate_course(installed)
        self.assertEqual(installed['lessons'],course['lessons'])
        html=render_reader(exported)
        self.assertIn('data:image/png;base64,',html)
        self.assertNotIn('src="/reader.js"',html)
        self.assertNotIn('/*ASTAR_',html)
        exported['title']='</script><script>alert(1)</script>'
        html=render_reader(exported)
        self.assertNotIn('</script><script>alert(1)',html)

    def test_untrusted_package_validation(self):
        make_book(self.source)
        course=self.convert()
        invalid=copy.deepcopy(course);invalid['lessons'][0]['panels'][0]['image']='../../private.txt'
        with self.assertRaises(ValueError):validate_course(invalid)
        invalid=copy.deepcopy(course);invalid['lessons'][0]['pageStart']='<img src=x>'
        with self.assertRaises(ValueError):validate_course(invalid)
        invalid=copy.deepcopy(course);invalid['lessons'][1]['id']=invalid['lessons'][0]['id']
        with self.assertRaises(ValueError):validate_course(invalid)

    def test_encrypted_pdf_is_reported(self):
        doc=pdf.open();doc.new_page();doc.save(self.source,encryption=pdf.PDF_ENCRYPT_AES_256,owner_pw='owner',user_pw='password');doc.close()
        with self.assertRaisesRegex(ValueError,'password'):self.convert()

    def test_split_preserves_every_character(self):
        value='αβγ \n  original words\twith spaces.\nAnother line.'
        self.assertEqual(''.join(split_text(value,3)),value)

    def test_isolated_stamp_removed_without_erasing_underlying_lesson(self):
        doc=pdf.open();page=doc.new_page(width=600,height=800)
        font=page.insert_font(fontname='helv')
        page.insert_text((60,300),'Leaves capture sunlight. Keep this learning text.',fontsize=12)
        baseline=page.get_pixmap(colorspace=pdf.csGRAY,alpha=False)
        stamp=doc.get_new_xref()
        doc.update_object(stamp,f'<< /Type /XObject /Subtype /Form /BBox [0 0 600 100] /Resources << /Font << /H {font} 0 R >> >> >>')
        doc.update_stream(stamp,b'BT /H 48 Tf 1 0 0 1 0 0 Tm (SCHOOL PUBLISHER) Tj ET')
        resource=int(doc.xref_get_key(page.xref,'Resources')[1].split()[0])
        doc.xref_set_key(resource,'XObject/Stamp',f'{stamp} 0 R')
        content=page.get_contents()[-1];doc.update_stream(content,doc.xref_stream(content)+b'\nq 0.7 0.7 -0.7 0.7 130 400 cm /Stamp Do Q\n')
        clean,removed=learning_pixmap(page,1)
        self.assertTrue(removed)
        self.assertEqual(clean.samples,baseline.samples)
        self.assertIn('SCHOOL PUBLISHER',page.get_text())
        self.assertIn('Leaves capture sunlight',page.get_text())
        doc.close()


if __name__ == '__main__':unittest.main()
