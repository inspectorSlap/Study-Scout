# Prospective search plan

Topic selected for its narrow computing scope and known connection to prior literature. This is a worked-example search, not a blinded novelty challenge: the agent has prior general knowledge of Eytzinger layouts. No paper was opened and no topic search was executed in this task before this plan and study controls were frozen. Do not claim an independent cold-start discovery experiment.

## Frozen bounds

- Two claims: single-threaded speed advantage; extension to concurrent readers.
- Sources: Crossref and OpenAlex metadata search, followed by public web discovery/primary-source inspection where API retrieval is incomplete.
- Initial search budget: three frozen queries against both metadata providers, one page of 10 results each (at most 60 result positions). Three web searches using the same initial query text. If an API call fails, retain its failure; do not silently substitute success.
- Follow-up budget: at most three registered terminology/citation/author queries prompted by discovered primary sources; at most six primary papers/articles inspected in detail. Record every follow-up query and its provenance.
- Screen every returned metadata candidate, retaining exclusions and reasons. Reviews/tutorials may be contextual leads but cannot establish the experimental claim.
- Initial evidence preference: publicly readable original papers with implementations and measurements; inspect methods/results, not just abstracts. Accessible author manuscripts count. Do not redistribute article text or PDFs; store links, locations, bibliographic metadata, and original paraphrases.
- Date cutoff: 2026-09-27. Apply during screening; the API adapters do not enforce this filter.
- Both PRECEDED and scores 4/5 remain provisional pending actual human review. Do not fabricate adjudicator identities, decisions, or stopping rounds.
- This is a budget-bounded example. It will report stopping NOT SATISFIED unless the existing complete-round rule is genuinely met. The expected delivery is a small useful case study, not an exhaustive systematic review.
- Record primary-source access failures and unavailable details. If C2 is not tested by located sources, say not established within this bounded search, not novel.

## Coding policy

Use the existing 0–5 equivalence scale. A paper directly testing all claim-critical dimensions can receive 5/PRECEDED provisionally; partial implementations or workloads receive PARTIALLY_PRECEDED, ADJACENT, or UNCERTAIN with missing criteria identified. For C1, concurrency is descriptive and not required. For C2, concurrency is required. A full-text methods/results inspection is necessary for a 4/5 proposal. Claims and criteria will not be changed after retrieval.
