# Methodology

StudyScout organizes an adversarial search: look for the strongest earlier evidence that reduces the distinctiveness of a proposed claim. Similar vocabulary is a discovery lead; experimental correspondence supports a judgment.

## Prospective controls

Write claims and comparison criteria before reviewing candidates. Freeze their exact bytes with the initial seed set and source policy. Subsequent revisions are new study versions, with reasons recorded. Do not redefine the original claim to accommodate an inconvenient paper.

## Independence and cold search

An operator can run a discovery agent in a fresh workspace containing only the frozen claim specification, search rules, and allowed source material. Keep previously collected candidate lists and other agents' conclusions outside that context. A second reviewer can independently inspect primary evidence after discovery.

Before injecting an external list, preserve the cold-pass files and a checksum manifest or version-control commit in private storage. Label the injected candidates and all descendants with their Stage 2 provenance. Scripts preserve labels; process isolation and context separation are operator responsibilities. Separate agents can still make correlated errors.

An optional planted-positive check can test retrieval sensitivity: an operator privately chooses a relevant paper and a random nonce, stores a commitment to their canonical representation, and reveals them only after the cold-pass corpus is frozen. Failure to retrieve the known item is a diagnostic limitation. This v0.1 does not automate commitment creation or verification; do not claim calibrated recall from the uncalibrated demo.

## Experimental comparison

For each serious candidate, inspect what was manipulated, the comparator, held-constant variables, measured outcomes, and uncertainty. Retain the exact table, figure, section, or page location. Keep source observations distinct from the coder's inference. Record rejected candidates with reasons rather than deleting them.

The default equivalence rubric is:

| Score | Meaning |
|---|---|
| 0 | No relevant experimental correspondence |
| 1 | Shared topic or motivation |
| 2 | Related mechanism, with a materially different experiment |
| 3 | Substantial correspondence with a missing decisive element |
| 4 | Close experimental correspondence requiring human adjudication |
| 5 | The claimed experimental result appears directly preceded; human review required |

A score is a proposal, not a probability. The public v0.1 fixes the 0–5 scale and review threshold; study-specific comparison dimensions are configurable. Changing the scoring policy itself requires an explicit software/protocol revision.

Allowed statuses: `PRECEDED`, `PARTIALLY_PRECEDED`, `ADJACENT`, `NOT_RELEVANT`, `UNCERTAIN`. Scores 4–5 and every `PRECEDED` or `PARTIALLY_PRECEDED` proposal require human review. A high-equivalence `UNCERTAIN` row can be a close test whose result does not establish the claim; the review packet calls out this distinction. Do not relabel such a result `CONTRADICTED` unless the implementation, comparator, and outcome justify that stronger claim. Primary-source access gaps should be visible. Neither source metadata nor a provider's publication type establishes peer review or experimental equivalence.

## Coverage and stopping

Expand through backward citations, forward citations, authors, and terminology. Record each expansion's parents and execution, including zero-result searches and failures. A source cap, access block, or local page budget is not exhaustion.

The computational rule checks two consecutive complete rounds without new high-equivalence candidates or productive families. A productive family is a newly recorded family containing a new candidate with effective score at least 3; high-equivalence means at least 4, or an effective `PRECEDED` status. Human-adjudicated scores replace proposals in these counts. Each round needs a nonempty trigger set, completed coverage along all four paths, and recorded round queries with completed source executions. A failed, capped, or manually stopped execution cannot support a `COMPLETE` coverage claim. The script verifies counts against the records supplied; it cannot determine whether unrecorded literature or uninspected candidates would change them.

Before closing, separately resolve or disclose pending screening, mandatory reviews, missing sources, and calibration failures. The generated matrix is a navigation aid, not a complete review report or proof of exhaustive search.

## Bounded conclusions

Report what was found within the searched sources and cutoff. Describe the closest precedent and the evidence supporting any remaining differences. Never turn “not found in this search” into “does not exist.” This workflow is for research comparison; it does not determine legal patent novelty or freedom to operate.
