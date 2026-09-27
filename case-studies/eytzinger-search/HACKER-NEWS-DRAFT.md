# Hacker News submission draft

Nothing has been submitted. Review and adapt this text before posting.

**Title:** Show HN: StudyScout – traceable prior-work checks for research claims

**URL:** https://github.com/inspectorSlap/Study-Scout

**Suggested first comment:**

I built StudyScout to make an agent-assisted literature search easier to inspect. You define a research claim and its comparison criteria, freeze them before searching, then retain the retrieval history, evidence locations, and provisional judgments. Strong matches require a human decision.

The repo includes a real, deliberately narrow computing example: Eytzinger array layout, software prefetching, and concurrent searches. It shows why a paper mentioning the right mechanism isn't enough—you need to check the actual comparator and workload.

You can replay the recorded example offline with Python's standard library. It includes the unsuccessful retrieval attempt and unresolved leads, and labels the human reviews as pending. Replay regenerates the reports; it doesn't repeat the search or run the cited performance benchmarks.

This is an early CLI toolkit, not an autonomous reviewer or a novelty detector. I'd particularly welcome feedback on the evidence schema, reproducibility, and whether the distinction between experimental similarity and support for a claim is clear.
