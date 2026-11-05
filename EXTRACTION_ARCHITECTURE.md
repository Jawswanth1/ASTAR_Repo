# Source-grounded extraction: current implementation

## Supported pilot scope

The representative source is the local 374-page Class VIII mathematics textbook. Digital English text is the first target. Scanned pages remain visible; OCR accuracy and multilingual structure are not benchmarked. The system is not ready for unattended publication.

## Pipeline

1. **Inspection and page extraction:** PyMuPDF extracts native blocks, line geometry, images and vectors. It renders an unmodified grayscale original page as well as the existing cleaned learning image. Optional Tesseract OCR remains a separate, explicitly labelled path. No generative rewriting is used.
2. **Immutable evidence:** every page keeps its raw text blocks, bounds, extraction method and original image. This includes introductory pages and answer sections that do not appear in lessons. A canonical checksum protects this layer during browser edits. Coordinates are PDF points in a top-left coordinate system.
3. **Interpretation:** deterministic rules propose sections, examples, solution blocks, exercises, numbered questions, subparts, option markers, captions, tables and visual regions. Objects reference exact source text spans or visible page bounds. `text` is derived from those spans; the untouched raw block is retained independently. Joining source lines uses newline separators and does not reconstruct mathematical notation.
4. **Relationships:** parent IDs capture proposed hierarchy. Exercise/number matches produce unverified answer candidates. Figure associations are provisional, and questions without a detected candidate are flagged. `lessonIds` connect text-based objects to current lesson blocks; image-only objects may have no lesson ID. Missing/ambiguous references never create an answer key.
5. **Review:** Structure review places original source and selected object side by side. Reviewers can change interpretation, numbering, parent IDs and relationship status; record a separate correction; and recover a missed object from a complete source block. All changes are saved locally. Original text remains unchanged. The existing lesson editor still controls student-facing lesson content; structural corrections are exported as editorial records and are not silently substituted into lessons.
6. **Validation/export:** package validation checks evidence checksums, source spans, pages, parent cycles, relationship targets and unchanged extracted text. The existing ASTAR JSON package includes the structural model and original page images. JSON schema version remains `astar-1` with optional, separately versioned `astar-structure-1` data, so older packages can still open.

## Separation of evidence and judgment

- `structure.evidence.pages`: unfiltered source blocks and original images.
- `structure.objects`: proposed interpretation and source references.
- `object.review`: unreviewed, needs-correction or checked, with reviewer note.
- `object.correction`: separate editorial transcription; never overwrites evidence.
- `object.links`: candidate, checked or rejected relationships. A checked relationship is a reviewer action, not proof of educational correctness.
- `benchmarks/representative-book`: full-book run, diagnostic sample, metrics and release gate.

## Known structural limits

- Numbering rules can confuse lists, formulas and exercises. Roman markers can be options, subparts or standalone questions.
- Continuation text and nested subparts remain provisional. A marker alone is not a complete correctly reconstructed question.
- Ruled tables are detected with PyMuPDF; cell content, spanning cells and borderless tables need separate annotation and review.
- Raw drawings can extend outside the visible page. Review regions use their visible intersection. A detected region is not a verified semantic figure.
- Mathematical superscripts, fractions, fonts and reading order are not solved by preserving text tokens. Source images remain the authority.
- An answer matching an exercise and number is a candidate only. Answer correctness, completeness and subpart mapping require review.
- Package size grows when original images are embedded. Existing import/export size limits still apply; a full-book JSON round trip must be measured separately from fixture round trips.

## Benchmark policy

Run `python tools/benchmark_structure.py`. It processes the whole representative book. The report scores only the explicitly reviewed diagnostic pages and states each denominator. Text presence, exact question boundaries, numbering, subpart markers and semantic association are separate measures. Unmeasured categories are never reported as 100%.

The initial sample is selected to expose known failures, not to estimate population accuracy. It cannot justify an overall textbook accuracy percentage. Next work is independent annotation of more exercises, complete diagram associations, formula/table fidelity and held-out chapters; the release gate stays closed until those checks pass.
