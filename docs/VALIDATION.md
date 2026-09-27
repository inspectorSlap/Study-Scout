# Validation record

Public preparation: 0.1.0.

## Completed locally

- Twenty offline tests pass on Python 3.14.
- The synthetic end-to-end demo runs from initialization through freeze, retrieval logging, duplicate-aware ingestion, evidence, review, validation, and matrix generation.
- Negative controls exercise changed claims/seeds, an attempted second freeze, unregistered criteria, missing query parents, and an unfrozen workspace.
- Retrieval tests distinguish source exhaustion, page budgets, provider result caps, rate limiting, HTML challenges, and malformed JSON using simulated responses.
- Review tests preserve provisional status and decision history, and verify that human-lowered scores affect matrix ranking.
- The export was assembled from an explicit selection of generalized scripts plus new public documentation and synthetic fixtures. No original Git history or research data directories were copied.
- A text scan checks known private study names, original machine paths, and common credential formats. A local Markdown-link check verifies document targets.

## Not established by these checks

- Live end-to-end operation against each provider, production rate-limit behavior, and continued API compatibility.
- The quality, completeness, or correctness of any real literature search.
- Independent agent containment, human identity, or a tamper-proof audit trail.
- Concurrent-writer safety or transactional recovery across CSV files.
- Exhaustiveness of semantic privacy review: inspect the staged public files before the first push.

CI is configured for Python 3.10, 3.12, and 3.14 on Ubuntu. That configuration will run once pushed; it is not a claim that those hosted runs have already passed.
