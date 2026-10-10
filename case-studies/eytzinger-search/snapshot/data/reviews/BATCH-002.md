# Human Review BATCH-002

Items: **1**

## 1. EV-000002 — Array Layouts for Comparison-Based Searching

- Paper / claim / experiment: `P-000012` / `C2` / `KM2017-F21`
- Provisional: **PARTIALLY_PRECEDED**, equivalence **3/5**
- Review focus: proposed precedence; check the claimed correspondence and missing criteria
- Primary-source state: `PRIMARY_SECTIONS_AND_FIGURES_INSPECTED`
- Inspected source/version: https://arxiv.org/pdf/1509.05053v2 (candidate metadata year: 2015)
- Evidence location: arXiv v2: section 5.1; Figure 21, printed pp.36-37 (PDF pp.39-40).
- Evidence excerpt: _Not recorded_
- Manipulation: 2, 4, and 8 reader threads on a shared array.
- Comparison: Unrolled branch-free Btree, not sorted binary search.
- Held constants: Same hardware and query workload within each reported comparison.
- Observable: Completion time for fixed searches per thread.
- Coder inference: Concurrency tested, but the specified comparator is absent from this figure.
- Uncertainty or missing element: Do not infer a sorted-array comparison from the broad summary. At eight threads the plotted layouts converge for large arrays.

### Reviewer response

- Decision:
- Replacement score:
- Replacement status:
- Reason:
- Additional source needed:
- Adjudicator name:
