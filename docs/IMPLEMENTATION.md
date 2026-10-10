# Implementation guide

## 1. Install and separate your workspace

Use Python 3.10 or newer. There are no third-party runtime dependencies. Run commands from the toolkit repository. On Windows use `py -3` if appropriate and set environment variables with PowerShell syntax.

For a real study, keep the workspace outside the public toolkit checkout. All scripts except initialization and the demo use `STUDYSCOUT_WORKSPACE`; without it they default to the repository's ignored `workspace/` directory.

```sh
python3 scripts/init_study.py --config /path/to/my-study.json --workspace /path/to/my-private-study
export STUDYSCOUT_WORKSPACE=/path/to/my-private-study
```

PowerShell equivalent: `$env:STUDYSCOUT_WORKSPACE = 'C:\path\to\my-private-study'`.

Initialization refuses an existing destination. For the supplied teaching example, use `examples/study.json` as the config and a new workspace. Do not present the demo's output as a literature result.

## 2. Define claims and criteria

Use `examples/study.json` as the structural template. Required fields are:

- `study_id`: a stable identifier for this version of the search.
- `title`: a human-readable description.
- `cutoff_date`: an ISO date, checked by the researcher when screening publications.
- `claims`: an array of unique IDs and concrete claim text. IDs may contain letters, digits, hyphens, and underscores.
- `criteria`: an object mapping criterion names to comparison questions.

Phrase claims so that a prior experiment could contradict or precede them. Record what changes, what stays fixed, and what is measured. Custom criteria are saved for each evidence row in `criteria_json`; every configured criterion must have a nonempty text value. These values are qualitative notes, not a controlled vocabulary or machine-comparable verdicts. The software checks coverage and presence, not the truth of your judgments.

## 3. Add seeds and freeze

Edit `data/searches/seed-queries.csv` inside the workspace. Its header is already present. Add rows like:

```csv
seed_id,track,ordinal,claim_ids,query_text,freeze_date
SQ-001,mechanism,1,C1;C2,cache replacement fixed memory budget workload shift,2025-12-31
```

Use your actual claim IDs, query, and freeze date. Ordinals start at 1 and are contiguous. Separate multiple claim IDs with semicolons. Use a CSV editor or Python's `csv` module to quote commas and line breaks correctly.

Inspect `control/SOURCE_REGISTER.csv` and disable unwanted API sources by setting `cold_allowed` to `FALSE` before freezing.

```sh
python3 scripts/validate_records.py
python3 scripts/freeze_study.py
python3 scripts/register_seed_set.py
```

The freeze hashes the exact study config, source register, and seed file bytes. It is a reproducibility check, not tamper-proof storage. Archive the manifest externally if stronger provenance is needed. A changed claim, criterion, source policy, or seed set requires a new versioned workspace; do not silently overwrite the old freeze.

## 4. Retrieve metadata

List supported providers:

```sh
python3 scripts/api_search.py --list-sources
```

An example real network request:

```sh
python3 scripts/api_search.py --source crossref --query-id Q-S1-000001 --execution-id R-S1-000001 --page-size 25 --max-pages 2
python3 scripts/ingest_results.py --execution-id R-S1-000001
python3 scripts/validate_records.py
```

Execution IDs are unique. Each new API execution records raw data, normalized rows, pagination state, counts, terminal disposition, the effective request URL with contact email redacted, and SHA-256 digests of returned raw payloads inside `parameters_json`. A page limit is `PAGE_LIMIT_REACHED`, not proof that the source is exhausted. `--filters` is rejected because provider-side filters are not implemented. In manually logged executions, `filters` describes operator-supplied context and does not prove that a provider applied a filter. Screen against `cutoff_date` yourself and record exclusions.

Ingestion preserves discovery routes and uses DOI, arXiv ID, or normalized title/year for candidate matching. Ambiguous identity collisions stop ingestion. Title/year matching is heuristic; inspect possible false merges and edition/version differences. Ingested candidates remain `UNVERIFIED` until inspected.

For manual retrieval, register the query and use `log_retrieval.py --help` to record the execution. Normalized import files use the header in `examples/results.csv`. A manual source can be added to the source register before freezing. Keep raw files and normalized result paths relative to the workspace where possible.

## 5. Expand queries with ancestry

```sh
python3 scripts/register_query.py --query-id Q-S1-000002 --origin TERMINOLOGY --query 'adaptive cache eviction' --track terminology --claims C1 --generation 1 --parent-query-id Q-S1-000001
python3 scripts/validate_records.py
```

Repeat parent arguments to record multiple origins. Paper and citation-edge parents are also supported. Record real parent rows before referencing them. A new query does not itself run a search.

Keep an initial cold pass separate from externally supplied candidate lists. After preserving a frozen cold-pass corpus, label injected material `STAGE_2_INJECTED` and its descendants `STAGE_2_DESCENDANT`; use S2 query and execution IDs. The toolkit labels this distinction but does not provision isolated agents or automatically freeze the transition. See the methodology for the operator's role.

## 6. Inspect evidence and code it

Open the primary source. Examine its intervention, comparison, held constants, outcomes, tables, and limitations. Copy `examples/evidence.json`, replace the synthetic contents, and supply the existing candidate ID and your claim ID. Put the exact inspected version or edition in `primary_source` and `evidence_location`; the candidate's publication year may refer to an earlier version. Confirm exact publication timing when the source and cutoff share a year.

```sh
python3 scripts/add_evidence.py /path/to/evidence.json
python3 scripts/validate_records.py
```

Supply `criteria_json` as a JSON-encoded string, as shown in the example. Missing evidence is `UNKNOWN` or an explicit uncertainty, not a positive match. Scores 4–5 require manipulation, comparison, held constants, and observable. The importer rejects duplicate paper/experiment/claim loci and post-cutoff publication years for proposed precedence. Exact dates, source revisions, and judgment quality still require inspection. It assigns provisional authority and requires human review for scores 4–5 and all precedence or partial-precedence proposals. It refuses to import a human decision as a new proposal.

## 7. Obtain and record human review

```sh
python3 scripts/build_review_batch.py --batch-id BATCH-001
python3 scripts/assign_review_batch.py --batch-id BATCH-001 --evidence-id EV-000001
```

The first command renders unassigned items. The second assigns the IDs actually included; repeat `--evidence-id` for multiple items. Give the rendered batch and primary sources to a human reviewer.

Use `examples/decisions.json` as the decision format, with the actual reviewer, date, reasons, and decisions. Then:

```sh
python3 scripts/apply_review_decisions.py /path/to/review-decisions.json
python3 scripts/validate_records.py
python3 scripts/build_matrix.py --output data/synthesis/matrix.md
```

Do not use the synthetic decision file in a real study. The program records a claimed human decision; it cannot authenticate the reviewer. Previous matrix bytes and applied decision payloads are saved in `data/reviews/history/`.

## 8. Evaluate stopping and write the report

Maintain the round, trigger, coverage, candidate-family, and evidence records described in the data model. Then run:

```sh
python3 scripts/check_stopping_rule.py
```

This checks the declared round counts and reports whether the last two consecutive rounds meet the computational null condition. Each round must have linked queries and source executions whose terminal states support completion; capped, failed, and manually stopped executions prevent a complete round. Human-adjudicated scores are used when present. Exit code 0 means the records are consistent; it does **not** mean stopping is satisfied. Unreviewed candidates and pending human review remain separate gates for the researcher. There is no automatic final novelty verdict.

Write the final report using `templates/REPORT.md`. State the search dates, sources, cutoff, closest precedent, unresolved gaps, and remaining differences.

After the report and all records are final, seal the full workspace and verify it before sharing a snapshot:

```sh
python3 scripts/seal_study.py
python3 scripts/seal_study.py --verify
```

The report seal covers candidate and evidence records, raw responses, reviews, and reports. It is separate from the pre-search control freeze. Any later file change invalidates the seal; archive the seal outside the workspace for stronger provenance. Hashes establish byte consistency, not that a search or judgment was correct.

## Provider notes

Optional credentials are read from the environment: `OPENALEX_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`, and `PRIOR_ART_CONTACT_EMAIL`. Do not put credential values in config, examples, commands committed to Git, or evidence records. `.env` files are ignored but are not automatically loaded.

- [OpenAlex authentication](https://help.openalex.org/api/authentication/): StudyScout sends an optional key as a bearer token. Keyless availability and budgets depend on the service.
- [Crossref REST API](https://github.com/CrossRef/rest-api-doc): contact email is used for polite requests.
- [Semantic Scholar API](https://www.semanticscholar.org/product/api): an optional key is sent in `x-api-key`; requests can be rate-limited.
- [arXiv API manual](https://info.arxiv.org/help/api/user-manual.html): the adapter converts query words to conjunctive `all:` terms; it is not a pass-through for arbitrary arXiv query syntax.
- [DBLP API](https://dblp.org/faq/How+to+use+the+dblp+search+API.html): metadata is returned from publication search.

The runner waits 3.1 seconds between pages and stops on rate limits or errors. It does not retry automatically. Use a fresh execution ID for a later attempt; there is no automatic cursor resume or concurrent writer support. Provider adapters are offline-tested, not live-certified for every provider.
