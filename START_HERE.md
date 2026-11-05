# ASTAR — Chapter 1

Double-click **start.bat**. The current app opens at **http://127.0.0.1:8790/**. Keep its terminal open while using ASTAR.

## Put ASTAR online

ASTAR can run in Docker on a host that supports containers. Build and start it
with `docker compose up --build -d`, then open `http://localhost:8080` to check
it. The named `astar_data` volume keeps uploaded books and prepared data across
container restarts. On a hosting provider, deploy this repository using its
Dockerfile support and configure persistent storage at `/data`; the app reads
the provider's `PORT` environment variable. The deployed container serves only
the current learning app; older studio and demo pages are not included.

The app does not have user accounts or sign-in. Restrict access using your
hosting provider's access controls before sharing the URL. Without that
restriction, anyone who can reach the site can upload books and use the app.
Back up the persistent data volume.

1. Start on the ASTAR screen and choose **Begin**.
2. Upload your textbook PDF and choose **Prepare Chapter 1**.
3. Use the numbered chapter circles and the on-screen left/right buttons. Only Chapter 1 is available.
4. Open Chapter 1, select a numbered lesson circle, then choose **Open lesson**.
5. Read the complete original textbook pages. Fractions, diagrams, tables and examples retain their printed layout. Copyable extracted text is available below each page.
6. Open **Practice**. Choose an MCQ answer for immediate feedback, or write a long answer and reveal hints one at a time. Written responses have a self-check checklist; they are not automatically graded.
7. Mark the lesson complete. Responses, hint progress, self-checks and completion save in this browser.

Thirty minutes is a study target, not a forced timer or a measured guarantee. The app preserves full source pages and whole question groups; some sessions continue practice from the preceding reading.

## Your Class VIII maths textbook

The local SCERT textbook's first chapter, **Rational Numbers**, is prepared and verified:

- Physical PDF pages **13–48**, corresponding to printed pages **1–36**.
- **21 sessions**, covering all chapter pages.
- **90 original question/activity groups** and **13 MCQ adaptations** anchored to original questions. Some checkpoints recur as review.
- Added answer choices, hints and worked explanations are identified as ASTAR learning aids.
- Chapter 2 and later chapters are not processed.

Prepared chapter: http://127.0.0.1:8790/#chapters/2a2b6a21579b4c1294b2ed0600bc27dd

## Other textbooks

Use an unlocked PDF up to 100 MB / 2,000 pages. If Chapter 1 and Chapter 2 bookmarks do not establish a reliable boundary, enter the first and last physical PDF page numbers of Chapter 1. The scope is capped at 100 chapter pages.

The importer preserves the full chapter page images even when native text is unavailable. Generic question detection and answer keys depend on readable PDF text. A generic MCQ is graded only when an explicit answer is attached to that question. Otherwise the response is recorded without inventing a correctness verdict. Scanned books may therefore have readable original pages but no interactive questions.

## Files and checks

- Current interface: static/learn/.
- Chapter importer, session planner and source-linked practice: astar_app/learn.py.
- Uploaded books and prepared chapters: learning-data/.
- Browser validation: test-results/learning/validation.json.
- Tests: tests/test_learn.py and tests/learn-browser.cjs.

The clean entry screen replaces the previous studio/demo/product navigation. Earlier source files and original assets remain stored separately and are not part of the new learning flow.
