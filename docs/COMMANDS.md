# Command reference

Run from the toolkit checkout. Set `STUDYSCOUT_WORKSPACE` for the private workspace, except when using the explicit initialization/demo `--workspace` argument. Mutation commands require a single writer.

## `init_study.py`

Create an empty, private study workspace from a JSON specification.

```text
usage: init_study.py [-h] --config CONFIG --workspace WORKSPACE

Create an empty, private study workspace from a JSON specification.

options:
  -h, --help            show this help message and exit
  --config CONFIG
  --workspace WORKSPACE
```

## `demo.py`

Run a synthetic, offline workflow in a NEW workspace. No network calls.

```text
usage: demo.py [-h] --workspace WORKSPACE

Run a synthetic, offline workflow in a NEW workspace. No network calls.

options:
  -h, --help            show this help message and exit
  --workspace WORKSPACE
```

## `freeze_study.py`

Freeze controls once, after validation. Revisions require a new workspace.

```sh
python3 scripts/freeze_study.py
```

## `release_guard.py`

Verify frozen study specification, source policy, and seed query bytes.

```sh
python3 scripts/release_guard.py
```

## `seal_study.py`

After the final report, hash every workspace file except the seal itself and an optional `.git` directory. Verify later against the exact file set and bytes. This is a consistency check, not independent proof of the research process.

```sh
python3 scripts/seal_study.py
python3 scripts/seal_study.py --verify
```

## `register_seed_set.py`

Register the checksum-frozen StudyScout seeds with deterministic Stage 1 query IDs.

```sh
python3 scripts/register_seed_set.py
```

## `register_query.py`

Append one StudyScout query and its complete one-to-many genealogy.

```text
usage: register_query.py [-h] --query-id QUERY_ID
                         --origin {AUTHOR,CITATION,CONJUNCTION,DISCOVERED,EXPERIMENTAL_SHAPE,INJECTED,SEED,TERMINOLOGY}
                         [--stage {STAGE_1_COLD,STAGE_2_DESCENDANT,STAGE_2_INJECTED}]
                         [--seed-id SEED_ID] [--query QUERY] [--track TRACK]
                         [--claims CLAIMS] [--parent-query-id PARENT_QUERY_ID]
                         [--parent-paper-id PARENT_PAPER_ID]
                         [--parent-edge-id PARENT_EDGE_ID]
                         [--expansion-round-id EXPANSION_ROUND_ID]
                         [--generation GENERATION] [--created-by CREATED_BY]
                         [--notes NOTES]

Append one StudyScout query and its complete one-to-many genealogy.

options:
  -h, --help            show this help message and exit
  --query-id QUERY_ID
  --origin {AUTHOR,CITATION,CONJUNCTION,DISCOVERED,EXPERIMENTAL_SHAPE,INJECTED,SEED,TERMINOLOGY}
  --stage {STAGE_1_COLD,STAGE_2_DESCENDANT,STAGE_2_INJECTED}
  --seed-id SEED_ID
  --query QUERY
  --track TRACK
  --claims CLAIMS
  --parent-query-id PARENT_QUERY_ID
  --parent-paper-id PARENT_PAPER_ID
  --parent-edge-id PARENT_EDGE_ID
  --expansion-round-id EXPANSION_ROUND_ID
  --generation GENERATION
  --created-by CREATED_BY
  --notes NOTES
```

## `api_search.py`

Run one released StudyScout query against one scholarly API with auditable pagination.

```text
usage: api_search.py [-h] [--list-sources]
                     [--source {arxiv,crossref,dblp,openalex,semantic-scholar}]
                     [--query-id QUERY_ID] [--execution-id EXECUTION_ID]
                     [--page-size PAGE_SIZE] [--max-pages MAX_PAGES]
                     [--filters FILTERS]

Run one released StudyScout query against one scholarly API with auditable
pagination.

options:
  -h, --help            show this help message and exit
  --list-sources
  --source {arxiv,crossref,dblp,openalex,semantic-scholar}
  --query-id QUERY_ID
  --execution-id EXECUTION_ID
  --page-size PAGE_SIZE
  --max-pages MAX_PAGES
  --filters FILTERS     Reserved; nonempty values are rejected because provider filters are not implemented
```

## `log_retrieval.py`

Append one immutable StudyScout source-execution record, including failures and zero results.

```text
usage: log_retrieval.py [-h] --execution-id EXECUTION_ID --query-id QUERY_ID
                        --source-id SOURCE_ID
                        [--parameters-json PARAMETERS_JSON]
                        [--filters FILTERS] [--started-at STARTED_AT]
                        [--completed-at COMPLETED_AT] [--page-size PAGE_SIZE]
                        [--pagination-start PAGINATION_START]
                        [--pagination-end PAGINATION_END] --pages PAGES
                        --result-count RESULT_COUNT
                        [--results-available RESULTS_AVAILABLE]
                        [--serious-candidates SERIOUS_CANDIDATES]
                        [--api-failure {TRUE,FALSE}]
                        [--api-truncated {TRUE,FALSE}]
                        --terminal {ACCESS_BLOCKED,API_FAILURE,API_RESULT_CAP,API_TRUNCATED,MANUAL_STOP,PAGE_LIMIT_REACHED,PENDING,QUERY_COVERAGE_COMPLETE,RATE_LIMITED,SOURCE_EXHAUSTED}
                        --status {COMPLETE,FAILED,BLOCKED}
                        [--raw-paths RAW_PATHS]
                        [--normalized-paths NORMALIZED_PATHS] [--notes NOTES]

Append one immutable StudyScout source-execution record, including failures
and zero results.

options:
  -h, --help            show this help message and exit
  --execution-id EXECUTION_ID
  --query-id QUERY_ID
  --source-id SOURCE_ID
  --parameters-json PARAMETERS_JSON
  --filters FILTERS
  --started-at STARTED_AT
  --completed-at COMPLETED_AT
  --page-size PAGE_SIZE
  --pagination-start PAGINATION_START
  --pagination-end PAGINATION_END
  --pages PAGES
  --result-count RESULT_COUNT
  --results-available RESULTS_AVAILABLE
  --serious-candidates SERIOUS_CANDIDATES
  --api-failure {TRUE,FALSE}
  --api-truncated {TRUE,FALSE}
  --terminal {ACCESS_BLOCKED,API_FAILURE,API_RESULT_CAP,API_TRUNCATED,MANUAL_STOP,PAGE_LIMIT_REACHED,PENDING,QUERY_COVERAGE_COMPLETE,RATE_LIMITED,SOURCE_EXHAUSTED}
  --status {COMPLETE,FAILED,BLOCKED}
  --raw-paths RAW_PATHS
  --normalized-paths NORMALIZED_PATHS
  --notes NOTES
```

## `ingest_results.py`

Ingest one normalized execution result without erasing duplicate discovery routes.

```text
usage: ingest_results.py [-h] --execution-id EXECUTION_ID
                         [--result-file RESULT_FILE] [--round-id ROUND_ID]

Ingest one normalized execution result without erasing duplicate discovery
routes.

options:
  -h, --help            show this help message and exit
  --execution-id EXECUTION_ID
  --result-file RESULT_FILE
  --round-id ROUND_ID
```

## `add_evidence.py`

Append an agent-proposed evidence record from JSON, deriving review requirements.

```text
usage: add_evidence.py [-h] record

Append an agent-proposed evidence record from JSON, deriving review
requirements.

positional arguments:
  record

options:
  -h, --help  show this help message and exit
```

## `build_review_batch.py`

Render a non-mutating human-review batch for mandatory StudyScout adjudication.

```text
usage: build_review_batch.py [-h] --batch-id BATCH_ID [--limit LIMIT]
                             [--output OUTPUT]

Render a non-mutating human-review batch for mandatory StudyScout
adjudication.

options:
  -h, --help           show this help message and exit
  --batch-id BATCH_ID
  --limit LIMIT
  --output OUTPUT
```

## `assign_review_batch.py`

Assign unbatched mandatory StudyScout evidence rows to one stable human-review batch.

```text
usage: assign_review_batch.py [-h] --batch-id BATCH_ID
                              --evidence-id EVIDENCE_ID

Assign unbatched mandatory StudyScout evidence rows to one stable human-review
batch.

options:
  -h, --help            show this help message and exit
  --batch-id BATCH_ID
  --evidence-id EVIDENCE_ID
```

## `apply_review_decisions.py`

Apply structured human decisions while retaining the original StudyScout proposal.

```text
usage: apply_review_decisions.py [-h] decisions

Apply structured human decisions while retaining the original StudyScout
proposal.

positional arguments:
  decisions

options:
  -h, --help  show this help message and exit
```

## `validate_records.py`

Validate study configuration, CSV relationships, evidence, and frozen controls.

```sh
python3 scripts/validate_records.py
```

## `build_matrix.py`

Render a deterministic StudyScout paper-by-claim matrix from evidence records.

```text
usage: build_matrix.py [-h] [--output OUTPUT] [--stdout]

Render a deterministic StudyScout paper-by-claim matrix from evidence records.

options:
  -h, --help       show this help message and exit
  --output OUTPUT
  --stdout
```

## `check_stopping_rule.py`

Recompute StudyScout round completeness, machine-null status, and stop eligibility.

```text
usage: check_stopping_rule.py [-h] [--write-status WRITE_STATUS]

Recompute StudyScout round completeness, machine-null status, and stop
eligibility.

options:
  -h, --help            show this help message and exit
  --write-status WRITE_STATUS
                        Optional output; omitted for read-only validation
```

## Exit status

Validation and stopping-checker exit 1 on inconsistent records. A successful stopping check may still report NOT SATISFIED. API execution exits 1 for provider failure/access blocks; a bounded page-limit result can exit 0 while remaining incomplete. Argument errors exit 2. Freeze/integrity failures stop the operation with a nonzero status.

## Replay a published case

`python3 scripts/replay_case.py --case case-studies/eytzinger-search --workspace workspace/eytzinger-replay` verifies hashes, copies the snapshot to a new workspace, validates the records, and reproduces the recorded outputs. It makes no network calls and refuses to overwrite an existing destination. Hashes check consistency, not authenticity.
