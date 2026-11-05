# Current release — 6 November 2026

Start with [START_HERE.md](START_HERE.md). **The current app is a fresh Chapter 1 learning flow:** ASTAR → textbook upload → chapter circles → lesson circles → full source reading and interactive practice. Run `start.bat` and use http://127.0.0.1:8790/. MCQs give verified feedback; written answers have progressive hints and self-checks. Only Chapter 1 is prepared. The material below documents the earlier textbook studio and is retained as historical implementation documentation.

# ASTAR textbook studio

A working local application for preparing textbook PDFs and exporting standalone
monochrome learning courses. It contains a Python preparation server and a browser
reader with no JavaScript framework, cloud API, accounts, CDN or remote fonts.

## Start on this computer

Python 3.11, PyMuPDF and Pillow are already available in the development environment.

1. Double-click `start.bat`, or run `python -m astar_app.server` from this folder.
2. Open **http://127.0.0.1:8765** in a browser. Keep the terminal running while
   importing and editing textbooks.
3. Choose **Prepare a textbook**, select a PDF, set the title and lesson settings,
   then choose **Prepare lessons**.
4. The **Needs attention** screen ranks likely problems, grouping shared source
   issues. Lessons that pass automatic checks do not require individual approval.
   Open flagged lessons to fix OCR or uncertain layout, or use All lessons to edit.
5. Choose **Offline reader** to download one HTML file. Copy that file to another
   computer and open it directly. It includes the course, scripts and PNG images;
   the preparation server and internet are not needed for reading.

If port 8765 is in use, run `python -m astar_app.server --port 8766` and use the
matching local address. This application listens only on 127.0.0.1.

## Install on another computer

Install Python 3.11 or later and run `setup.bat` (or
`python -m pip install -r requirements.txt`) once. Installation needs internet or
locally supplied dependency wheels. Conversion and reading then work offline.
Tesseract is optional; see below for scanned books.

## What works

- PDF uploads up to 200 MB and 2,000 pages; digital text is extracted without
  paraphrasing. Original words, punctuation, Unicode and page references are kept.
- Chapters from PDF bookmarks, conservative English heading detection, or an
  explicit chapter plan using `PDF page number | Chapter title`. Preliminary pages before
  the first numbered chapter are omitted from lessons and logged. Chapter titles
  are taken from page headings where bookmarks are filenames or incomplete.
- Lesson sizing with a requested word budget and minimum course count. The
  default target is 150 lessons. Splitting prefers sentence endings and text block
  boundaries, and never pads a short book with invented or duplicated text.
  Approximately 60 words per text lesson limits the count target; a sparse book can
  finish below the requested count, with an explicit warning.
- Every PDF page rendered as a 1-bit black/white PNG, including bitmap and vector
  diagrams, tables and equations. Choose pattern shading or a fixed threshold.
- Review with editable text blocks, chapter assignment, notebook-prompt flags,
  lesson split/merge, editable titles, source image comparison and review markers.
- Teacher-entered MCQs between text blocks, with explicit checked answer keys,
  and notebook questions in the middle or at the end. Added questions are labelled
  separately from original textbook prompts. No generated answers are inferred.
- Numbered chapter and lesson circles; reader text sizing; local completion and
  resume state; progress backup/import; a three-button layout with keyboard input.
- Portable `.astar.json` packages including images for transfer between studios.
  Package inputs are validated and course JSON is saved through atomic replacement.

## Scanned textbooks and languages

The OCR adapter uses the local Tesseract executable and `pytesseract`. Install
Tesseract and the language data you need, then restart the server. The import screen
reports whether the executable is available. Windows' conventional installation at
`C:\Program Files\Tesseract-OCR\tesseract.exe` is detected automatically; alternatively
set `ASTAR_TESSERACT` to an executable path or put Tesseract on PATH.

Use codes such as `eng`, `hin`, or `eng+hin`. OCR runs on pages with little native
text. Its confidence and errors appear in the report. If OCR is unavailable or
fails, the source page image is still retained and readable. The user must then
transcribe the text or install OCR and re-import. **Tesseract is not installed in
this development environment, so real OCR recognition has not been verified here.**
Native PDF text supports Unicode; firmware font coverage is not established.

## Storage and backups

`data/<course-id>/` holds the original PDF, page PNGs and `course.json`. No books
are uploaded to a remote service. Keep this directory for studio backups, or export
an ASTAR package. Package imports generate a fresh local ID; progress is associated
with the source PDF checksum and stable lesson IDs. Significant lesson edits may
change how old completion records apply, so check progress after restructuring.

Student progress lives in browser localStorage. It can be cleared by the browser
and may be restricted for local files, especially on mobile browsers. Use **Export
progress** regularly; the reader reports storage failures. Saving progress does not
rewrite the downloaded HTML file. Each student should use their own browser profile
or device. Use one studio tab when editing; concurrent edits have no conflict merge.

## Current limits

- This is a local software release, not physical device firmware. Validation now
  includes the user-imported 374-page Class VIII mathematics PDF as well as
  generated fixtures. The actual PDF remains local and is not bundled with tests.
- The automatic splitter uses text lengths, sentences, page references and chapters;
  it does not fully understand a subject's concepts or teaching sequence. Review
  boundaries and adjust them before teaching.
- Standard reading view now includes extracted monochrome diagrams. Mathematical
  pages with stacked notation use one coherent cropped learning region per lesson
  to preserve fractions, tables and diagrams. Those pages can exceed the requested
  word budget. This is layout preservation, not semantic equation reconstruction
  or automatic diagram redrawing. Original page views remain available.
- Textbook prompts are detected heuristically and remain in the source text.
  Original MCQs are not yet parsed reliably into interactive options. Additional
  practice is authored manually. Long-answer responses are written on paper and
  are not automatically graded.
- Complex columns, sidebars, embedded font encodings, equations, tables and OCR
  reading order can need correction. The original page image is the reference.
  Colour-only distinctions can be lost in monochrome; review those diagrams.
- Chapter heading detection is English; other languages can use bookmarks or a
  manual chapter plan. Spaceless scripts do not yet have language-specific lesson
  word segmentation. Mixed scanned/digital pages may need manual OCR/transcription.
- Three-button view is a browser interaction preview, not a pixel-accurate e-paper
  emulator. Menu selection and lesson scrolling/continuation use three buttons;
  authoring, answer selection and some navigation still use ordinary browser controls.
- Large embedded courses require browser RAM. The single-file export favours
  portability over the smallest possible device footprint. Target hardware, screen,
  SD-card format and firmware integration remain to be specified and measured.
- Password-protected PDFs need an unlocked copy. Failed imports can leave a source
  folder without course.json; it is not listed as an installed course.

## Verification

```powershell
python -m unittest discover -s tests -v
node --check static/app.js
node --check static/reader.js
```

Twenty Python tests cover text/character preservation, vector diagrams, scanned-page
fallback, manual chapters, encrypted PDFs, untrusted input, package round trips and
a 20-chapter / 150+ lesson fixture.

`tests/browser.cjs` is an optional Playwright workflow test, independent of the app.
Install Playwright only if you want to run browser tests. Supply the package path
as `ASTAR_PLAYWRIGHT` and a Chromium executable as `ASTAR_CHROMIUM` if needed. It
expects an original sample PDF at `test-results/sample-science.pdf`, generated with:

```powershell
python -c "import sys; from pathlib import Path; sys.path.insert(0,'tests'); from test_conversion import make_book; Path('test-results').mkdir(exist_ok=True); make_book(Path('test-results/sample-science.pdf'))"
node tests/browser.cjs
```

The browser test covers upload, editing, teacher MCQs and notebook questions, saves,
split/merge, package transfers, mobile width, saved progress, and opening the exported
HTML from a local file with networking disabled. Screenshots and machine-readable
results are written to `test-results/`. It creates sample courses in the local library.

## Code map

`astar_app/converter.py` handles extraction, OCR, images and lesson construction.
`storage.py` validates and transfers courses. `server.py` provides the local API
and standalone export. `static/app.js` is the preparation interface;
`static/reader.js` is the shared reader embedded into exported HTML.

## Document analysis and targeted review (v0.2)

The importer analyzes the whole document before making lessons. It identifies
numbered-chapter starts, removes preliminary and reference matter from the lesson
stream, filters repeated headers, footers, publisher watermarks, page numbers and
clear promotional side text, and keeps educational callouts and captions. Simple
two-column layouts are read one column at a time. Unknown side notes are retained
and flagged instead of being silently discarded.

Every exclusion has a page, bounding box, reason and original text in the Conversion
report. Excluded text can be restored into a lesson. The original PDF is retained.
Automatic checks and human review are recorded separately; an automatic pass does
not mean a person verified the content. Risk is an ordinal rule-based diagnostic,
not a calibrated percentage or factual-accuracy guarantee.

Needs attention groups repeated source problems, orders high-risk missing/garbled
text before ambiguous margins, and lets you save and move to the next problem.
Ordinary textbook questions no longer create a review task just because they were
detected. Export and reading do not require approval of all lessons.

Choose **Rebuild import** on an older course to create a new analyzed course while
retaining the old course and its edits. Rebuilding needs its original source PDF;
transferred packages without that PDF must be re-imported from the original file.

`tests/quality-browser.cjs` tests ranked triage, grouped issues, targeted resolution,
exclusion restore, mobile width and, when ASTAR_REAL_COURSE is set, a full real-book
rebuild. The real-book test checks 15 chapters, skips the first 12 preliminary
pages and the answer/reference appendix, and verifies mathematical layout crops.

Rendering v2.1 removes a large diagonal text stamp only when it is an isolated, matching text-only PDF Form XObject. Its stream is restored immediately in memory and the source PDF is never overwritten. This avoids erasing learning text underneath the stamp. Unknown or mixed graphic stamps are preserved. The regression test compares the clean rendered pixels against an unstamped baseline and verifies that the original text remains in the PDF.
#   A S T A R _ R e p o  
 #   A S T A R _ R e p o  
 