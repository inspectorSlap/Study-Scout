# Evidence report

## Frozen questions

The exact claims and six criteria are in [study.json](study.json). C1 requires breadth-first Eytzinger layout, branch-free traversal, explicit prefetching, an optimized sorted-array comparator, measured performance, and a static RAM-resident working set above last-level cache. C2 additionally requires concurrent independent readers and retention of the advantage by the same implementation.

## Primary evidence

**Khuong and Morin, Array Layouts for Comparison-Based Searching.** [arXiv v2, 2017](https://arxiv.org/abs/1509.05053v2), [journal DOI](https://doi.org/10.1145/3053370). The 2015 preprint and 2017 journal metadata are one research family. Evidence locations refer to the 49-page v2 manuscript, not the earlier 46-page draft.

Figure 22 (printed p.38; PDF p.41) compares prefetched, branch-free Eytzinger and binary search beyond the L3 boundary. That supports a provisional C1 precedent. Figure 21 (printed p.37; PDF p.40) tests 2, 4, and 8 threads, but its comparator is a Btree. It does not directly establish C2's sorted-array comparison. The plotted advantage narrows, reaching approximate parity at eight threads for large arrays. Relevant methods are in sections 2, 3.2.3, 5.1 and 5.2. Both figures were visually inspected.

**Kmječ and Groot Koerkamp, Binary search variants and the effects of batching (February 2025).** [Original benchmark report](https://curiouscoding.nl/posts/binsearch/), sections 1.3 and 5. The authors compare batched, prefetched implementations using eight threads and arrays up to 1GB on a Ryzen 4750U. They report similar performance for Eytzinger and binary search. Batching differs between implementations, so this is close counterevidence to an unqualified advantage, not an exact replication or a universal refutation. This source is an original experimental blog; it is not treated as peer reviewed. Methods and results text were inspected; its code and raw measurements were not independently verified.

## Reading the judgments

- EV-000001: C1, **5 / PRECEDED**, requires human review.
- EV-000002: C2, **3 / PARTIALLY_PRECEDED**, missing decisive comparator in the inspected threaded figure.
- EV-000003: C2, **4 / UNCERTAIN**, close experiment with a different implementation and an outcome that does not establish the claimed advantage; requires human review.

All three are agent proposals. No benchmark was executed locally and no reviewer acceptance was invented. The matrix's lack of a mandatory review flag for the score-3 row does not make it human-approved.

## Coverage and unresolved work

The study controls were frozen before this task's retrieval; topic selection was informed by prior model knowledge. A targeted follow-up was registered after the comparator mismatch was noticed, with both the original query and paper as parents. It located the later report. Other promising leads remain visible for a subsequent, separately recorded expansion.

The corpus screening table includes unresolved computing papers, rather than rejecting them for lack of inspection. The preprint/journal pair is linked by FAM-001 and coded once. Dates on selected sources precede the cutoff; unresolved records with only year metadata are not assumed to pass exact-date screening.

This run demonstrates retrieval, provenance, experiment comparison, and review preparation. It does not demonstrate exhaustive coverage, calibrated recall, independent agent agreement, or completed human adjudication. The generated stopping report correctly remains **NOT SATISFIED**. Finish the unresolved leads, source failures, and expansion rounds before making a broader literature claim.
