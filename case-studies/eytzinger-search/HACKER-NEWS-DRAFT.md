# Hacker News submission draft

Nothing has been submitted. Review and adapt this text before posting.

**Title:** Show HN: StudyScout – inspectable prior-work searches for research claims

**URL:** https://github.com/inspectorSlap/Study-Scout

**Suggested first comment:**

I built StudyScout because I wanted an agent-assisted literature search whose result I could audit. You write narrow claims and comparison criteria, freeze the starting plan, then keep the query ancestry, retrieval limits, source locations, experiment-level comparisons, and provisional judgments. Strong or partial precedence proposals go to human review.

I work in AI, so I picked an Eytzinger-layout question whose answer I did not know for the worked case. A frozen seed query led to a paper that appears to precede one claim. A threaded result in the same paper uses a different comparator, while a later close benchmark reports near parity under a different implementation. That leaves the second claim unresolved. The case has 13 candidates awaiting full text, three pending human reviews, and a stopping condition that is not satisfied.

You can replay the recorded case offline with Python's standard library. It verifies the published snapshot and regenerates the matrix and stopping report byte-for-byte. It does not rerun the search, independently code the papers, or rerun the benchmarks.

This is an early CLI toolkit, not an autonomous reviewer or a novelty detector. I'd welcome criticism of the evidence schema, the stopping rule, and how to represent a close experiment whose outcome does not support the claim.
