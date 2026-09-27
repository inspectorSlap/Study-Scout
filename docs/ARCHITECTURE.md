# Architecture and extension

StudyScout 0.1 is a collection of standard-library Python scripts. The public toolkit is separate from a private study workspace. No model SDK, orchestration platform, or database is required.

```text
study.json + seed queries + source register
                 |
           freeze / verify
                 |
query genealogy -> API/manual retrieval -> raw files + execution ledger
                                             |
                                  candidate + discovery records
                                             |
                        primary-source inspection and evidence coding
                                             |
                          human review -> matrix + bounded report
```

## Modules

- `rig_common.py`: workspace selection, study configuration, enums, and CSV helpers.
- `schemas.py`: exact column order and identifier patterns. This is the schema authority.
- `init_study.py`, `freeze_study.py`, `release_guard.py`: workspace creation and control integrity.
- Query, retrieval, ingestion, and review scripts: small command-line operations over explicit files.
- `validate_records.py`: configuration, schema, relationship, and review checks.
- `check_stopping_rule.py`: a separate check of expansion-round declarations.
- `api_search.py`: provider URL builders, parsers, bounded sequential requests, and execution logging.

The search toolkit does not implement the separate two-agent software-testing harness. Its agent brief supports a human-supervised literature workflow.

## Add comparison criteria

Edit the `criteria` object before freezing. Include exactly those names in each evidence record's `criteria_json`. Existing scripts do not need to change for a new subject area. The default score scale and mandatory review threshold remain fixed.

## Add a provider

For a manual source, add a source-register row before freeze and use `log_retrieval.py`. For an API adapter, add a URL builder and a parser returning `Page`, then register a `Source` in `api_search.py` and add it to initialization's source list. Maintain the normalized result header. Add offline tests for an empty page, a populated page, continuation, truncation, and error responses. Read the provider's current documentation before enabling live use.

Never log authorization headers or credential-bearing URLs. Preserve a failure as a failure. Do not infer source exhaustion from a rate limit or local page budget. New schema fields require changes to schemas, writers, validators, examples, tests, and documentation together.

## Operational boundaries

CSV mutation is single-writer. Do not run concurrent writers against one workspace. Several operations touch multiple files and are not transactional; preserve backups and validate after interruption. Human review changes save the prior evidence matrix and decision payload. Other record edits require the operator's private versioning/backups.

Hash manifests detect byte changes relative to a manifest; they do not authenticate its author or prevent rewriting the entire workspace. Stage labels do not enforce process isolation. The toolkit neither supplies a sandbox nor verifies that a named reviewer is human.

The included parsers use standard XML/JSON handling and bounded page counts. Live provider responses remain external input. No provider response is executed as code. Workspaces may contain sensitive search text and copyrighted material; keep them separate from toolkit releases.
