# ASTAR textbook app — verification

4 November 2026, Asia/Kolkata.

## Executed checks

- 22 Python tests passed. These cover text preservation, front matter and page furniture filtering, retained learning callouts, column order, equations, scanned-image fallback, encrypted-PDF rejection, package validation, export/import, unit boundaries and session planning.
- The session tests compare all extracted words before and after regrouping, per unit; original questions remain and no generated assessment items are added.
- Connected drawing parts are merged before cropping. A four-page fixture now produces one complete figure per page, with captions retained.
- Browser journey passed: PDF upload, invalid timing feedback, unit-count mismatch warning, source comparison, offline HTML export, navigation, completion persistence after reload, 390px layout, offline textbook questions and images. No JavaScript page errors. Evidence: `test-results/sessions-browser-results.json`.
- Visually inspected desktop import, mobile import and mobile offline reader screenshots. Corrected diagram fragmentation identified during that inspection.
- JavaScript syntax checks and Python launcher compilation passed. The launcher started the application and opened the browser on port 8780. Readiness probing was then adjusted to read the home page instead of repeatedly invoking the slower OCR-status endpoint.
- Full existing Class VIII mathematics PDF processed: 374 pages, 15 units, 61 draft study sessions, first learning page 13. Course schema validation passed. Evidence: `test-results/real-session-check/result.json`. This is conversion evidence, not an educational review of all 61 sessions.

## Consolidation

Three historical ASTAR folders moved under `creative/`. Nineteen byte-identical copied files removed after SHA-256 comparison with retained files. Unique historical files and the active textbook library remain. Exact operations are in `ORGANIZATION_LOG.json`.

## Remaining limits

- 30 minutes is a configurable planning target, using reading pace and practice allowance; real workloads vary. Image-only pages have unknown reading time and require review.
- OCR is not installed on this computer. Scanned pages remain available as images with warnings; OCR recognition was not verified.
- Automatic removal is heuristic. Review the exclusion log and restore learning text if necessary. Chapter-level textbook questions remain in their original location.
- No guarantee is made for every PDF, exact semantic reading order, all languages or all mathematical notation. Original source images are retained for comparison.
- Earlier creative launch work remains incomplete and archived; it is not represented as a completed launch package.
