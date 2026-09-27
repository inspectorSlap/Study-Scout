# Human Review BATCH-001

Items: **2**

## 1. EV-000001 — Array Layouts for Comparison-Based Searching

- Paper / claim / experiment: `P-000012` / `C1` / `KM2017-F22`
- Provisional: **PRECEDED**, equivalence **5/5**
- Primary-source state: `PRIMARY_SECTIONS_AND_FIGURES_INSPECTED`
- Evidence location: arXiv v2: sections 2, 3.2.3, 5.2; Figure 22, printed p.38 (PDF p.41).
- Evidence excerpt: _Not recorded_
- Manipulation: Eytzinger layout with branch-free traversal and software prefetch.
- Comparison: Branch-free sorted-array binary search with prefetch.
- Held constants: Same hardware and query workload within each reported comparison.
- Observable: Wall-clock search time.
- Coder inference: Direct precedent within reported settings.
- Uncertainty or missing element: Historical hardware; not a universal speed guarantee. Benchmarks not independently rerun.

### Reviewer response

- Decision:
- Replacement score:
- Replacement status:
- Reason:
- Additional source needed:
- Adjudicator name:

## 2. EV-000003 — Binary search variants and the effects of batching

- Paper / claim / experiment: `P-000049` / `C2` / `CC2025-S5`
- Provisional: **UNCERTAIN**, equivalence **4/5**
- Primary-source state: `PRIMARY_METHODS_RESULTS_TEXT_INSPECTED`
- Evidence location: Sections 1.3, 3.4, and 5; final multithreaded comparison.
- Evidence excerpt: _Not recorded_
- Manipulation: Batched, prefetched Eytzinger with eight threads.
- Comparison: Batched, prefetched sorted binary search.
- Held constants: Ryzen 4750U, 1.7GHz, turbo/SMT disabled; Rust; same benchmark setup.
- Observable: Amortized query time, five repeats, medians and spread.
- Coder inference: Close experimental comparison, but authors report near parity rather than a retained throughput advantage.
- Uncertainty or missing element: Different implementation with batching (Eytzinger 16, binary search 32); not the identical implementation in C1. Original blog, not established peer review. Underlying data/code not independently verified.

### Reviewer response

- Decision:
- Replacement score:
- Replacement status:
- Reason:
- Additional source needed:
- Adjudicator name:
