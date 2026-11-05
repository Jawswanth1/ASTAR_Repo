# Extraction benchmark — representative textbook

NOT READY for unattended educational publication. Sample metrics do not establish full-book accuracy.

Full run: 374 pages, 15 units, 61 sessions.

## Reviewed diagnostic sample

| Metric | Passed / checked | Percent | Meaning |
| --- | --- | --- | --- |
| paragraph_text_presence | 3 / 3 | 100.0% | Three reviewed prose spans on page 54; not paragraph segmentation or mathematical fidelity. |
| question_text_exact_match | 6 / 6 | 100.0% | Exact normalized prose and boundary match for six reviewed prompts from exercise 15.6, page 351. Superscript-bearing questions excluded. |
| question_numbering | 10 / 10 | 100.0% | Expected numbers 1–10 on page 351. Extra detections recorded separately. |
| subquestion_marker_recall | 5 / 5 | 100.0% | Markers under exercise 2.2 question 1, page 57. Does not certify complete diagram-to-subpart association. |
| verified_diagram_associations | 0 / 1 | 0.0% | Question 15.6/7 has a diagram on page 351. No correct association has been independently verified; this is an unmet review gate, not a measured diagram-recall rate. |
| answer_option_completeness | 0 / 0 | Not measured | No independently annotated MCQ in this diagnostic sample; not measured. |
| page_reference_accuracy | 10 / 10 | 100.0% | Physical PDF page references of the ten sampled questions. |
| question_reading_order | 1 / 1 | 100.0% | Question-number sequence on page 351, not full-book visual reading order. |
| structural_reconstruction | 4 / 4 | 100.0% | Four sampled section/example/exercise boundaries. |
| answer_candidate_mapping | 10 / 10 | 100.0% | Unique number-based candidate mappings to ten source answer entries; duplicates fail the check. All mappings remain unverified and unusable for automatic grading. |

## Limits

- Selected diagnostic pages, not a randomized or exhaustive gold corpus.
- Raw source preservation is not semantic extraction accuracy.
- Mathematics, table cells, graphical subparts and whole-book reading order still require independent annotation.
- No benchmark score is based on a generated answer key.