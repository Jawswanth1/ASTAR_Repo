# ASTAR extraction reliability handoff

## Delivered

- Unfiltered, source-grounded evidence for all 374 pages of the representative textbook, including answers and excluded introductory material.
- A separate structural model with exact source spans, geometry, provisional hierarchy, question/subpart detection, visual/table candidates and unverified answer relationships.
- Side-by-side source review with persistent corrections, review states, relationship inspection and recovery of missed source blocks.
- A repeatable benchmark, independently checked diagnostic sample and explicit release gate.
- A full structured textbook package: `benchmarks/representative-book/textbook.astar.json`.

## Use

The dedicated review server was started at **http://127.0.0.1:8782/#course/11111111111111111111111111111111/structure**. Open PDF page 351 to inspect exercise 15.6, or page 367 for its answer entries.

If that server is no longer running, use this command from the ASTAR folder:

```text
python -m astar_app.server --port 8782 --data-dir benchmarks/representative-book
```

The normal `start.bat` starts the updated app on port 8780 after its previous instance is closed. Existing courses need Rebuild import to acquire structural evidence; the original library remains intact.

## Executed verification

- A 26-test regression run passed. Five focused structural tests also passed after the final parsing fixes, including the newly added formula/answer-section regression.
- Fixture browser tests passed for side-by-side review, correction persistence, unchanged evidence, source-image export, answer-page review and mobile width.
- Full-book browser review passed: ten question objects on page 351, ten answer objects on page 367, original page image decoded, no JavaScript page errors.
- Full-book export/import passed: **374 source pages, 1,245 embedded PNGs, 17,659 structural objects, 84,719,840-byte JSON package**. All images were decoded/verified during import; evidence hashes, objects and relationships matched after the round trip.
- Desktop and mobile review screenshots were visually inspected. A final small layout change made relationships scrollable and added source-inspection/return controls; JavaScript syntax checks passed. That final layout adjustment did not receive another browser run because automatic approval review reached the account usage limit.

## Benchmark result and limits

See `benchmarks/representative-book/BENCHMARK_REPORT.md` for the complete denominators. In the reviewed diagnostic sample, six prose prompts matched exactly after whitespace normalization, all ten question numbers and page references were retained, and five subpart markers were found. Ten source answer entries had unique candidate mappings. These results do not establish full-book accuracy.

The release gate remains **NOT READY for unattended educational publication**. Precise diagram associations, mathematical fidelity, table-cell correctness, MCQ completeness and held-out chapters require further independent annotation. Counts of detected figures, tables or questions are candidate counts, not verified content counts. Structural corrections are editorial records; the lesson editor still controls student-facing text. No generated answer key was introduced.

## Operational limitation

The attempted restart of the older server on port 8780 was not executed: automatic approval review could not complete because the account usage limit was reached. This was a review-service failure, not a determination that the command was unsafe. The dedicated review server on port 8782 had already started and passed the full-book browser check.
