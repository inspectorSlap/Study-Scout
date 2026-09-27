# Data model

Each workspace has `study.json`, `control/`, and `data/`. CSV headers are exact and ordered; scripts use UTF-8 and LF output. `scripts/schemas.py` is the machine-readable schema authority.

## Controls

`study.json` defines claim IDs, text, cutoff, and comparison criteria. `control/SOURCE_REGISTER.csv` lists allowed providers. `control/freeze.json` binds these files and the seed registry by SHA-256.

## Record tables

### `data/searches/seed-queries.csv`

Primary identifier: `seed_id`; pattern: `SQ-\d{3}`.

Columns: `seed_id`, `track`, `ordinal`, `claim_ids`, `query_text`, `freeze_date`.

### `data/searches/queries.csv`

Primary identifier: `query_id`; pattern: `Q-S[12]-\d{6}`.

Columns: `query_id`, `stage`, `query_origin`, `seed_id`, `parent_query_id`, `parent_paper_id`, `parent_edge_id`, `expansion_round_id`, `generation`, `track`, `claim_ids`, `query_text`, `created_date`, `created_by`, `notes`.

### `data/searches/query-parents.csv`

Primary identifier: `parent_link_id`; pattern: `QP-S[12]-\d{6}`.

Columns: `parent_link_id`, `query_id`, `parent_type`, `parent_id`, `relation`, `round_id`, `created_date`, `notes`.

### `data/searches/retrieval-ledger.csv`

Primary identifier: `execution_id`; pattern: `R-S[12]-\d{6}`.

Columns: `execution_id`, `query_id`, `stage`, `source_id`, `source_name`, `access_method`, `parameters_json`, `filters`, `run_started_at`, `run_completed_at`, `requested_page_size`, `pagination_start`, `pagination_end`, `pages_retrieved`, `result_count`, `results_available`, `serious_candidate_count`, `api_failure`, `api_truncated`, `terminal_condition`, `status`, `raw_response_paths`, `normalized_result_paths`, `notes`.

### `data/searches/search-log.csv`

Primary identifier: `event_id`; pattern: `E-\d{6}`.

Columns: `event_id`, `timestamp`, `phase`, `stage`, `event_type`, `input_snapshot`, `output_files`, `unresolved_access`, `human_review_state`, `details`.

### `data/searches/citation-chains.csv`

Primary identifier: `edge_id`; pattern: `X-\d{6}`.

Columns: `edge_id`, `stage`, `source_paper_id`, `target_paper_id`, `expansion_path`, `direction`, `round_id`, `query_id`, `discovered_date`, `disposition`, `notes`.

### `data/searches/expansion-rounds.csv`

Primary identifier: `round_id`; pattern: `ROUND-S1-\d{3}`.

Columns: `round_id`, `stage`, `ordinal`, `started_at`, `completed_at`, `trigger_snapshot`, `trigger_paper_count`, `new_candidates_count`, `new_provisional_ge4_count`, `new_productive_family_count`, `complete`, `machine_null`, `notes`.

### `data/searches/expansion-coverage.csv`

Primary identifier: `coverage_id`; pattern: `COV-S1-\d{6}`.

Columns: `coverage_id`, `round_id`, `paper_id`, `backward_status`, `forward_status`, `author_status`, `terminology_status`, `completed_at`, `notes`.

### `data/searches/round-triggers.csv`

Columns: `round_id`, `paper_id`, `trigger_status`, `trigger_score`, `snapshot_date`, `notes`.

### `data/corpus/candidates.csv`

Primary identifier: `paper_id`; pattern: `P-\d{6}`.

Columns: `paper_id`, `title`, `authors`, `year`, `venue`, `url`, `doi`, `arxiv_id`, `source_found`, `stage`, `peer_reviewed`, `retrieved_date`, `verification_state`, `disposition`, `rejection_reason`, `first_seen_round_id`, `family_id`, `notes`.

### `data/corpus/discoveries.csv`

Primary identifier: `discovery_id`; pattern: `D-\d{6}`.

Columns: `discovery_id`, `paper_id`, `query_id`, `execution_id`, `stage`, `track`, `source`, `source_position`, `discovered_date`, `route_type`, `notes`.

### `data/corpus/candidate-families.csv`

Primary identifier: `family_id`; pattern: `FAM-\d{3}`.

Columns: `family_id`, `label`, `definition_basis`, `first_seen_round_id`, `created_date`, `provenance_stage`, `notes`.

### `data/coding/evidence-matrix.csv`

Primary identifier: `evidence_id`; pattern: `EV-\d{6}`.

Columns: `evidence_id`, `experiment_id`, `paper_id`, `claim_id`, `stage`, `title`, `authors`, `year`, `venue`, `url`, `doi`, `source_found`, `retrieved_date`, `verification_state`, `primary_source`, `manipulation`, `comparison`, `held_constants`, `observable`, `equivalence_score`, `evidence_quote`, `evidence_location`, `coder_inference`, `criteria_json`, `uncertainty`, `status`, `rejection_reason`, `manual_review_required`, `manual_review_status`, `review_batch_id`, `reviewer_decision`, `reviewer_notes`, `reviewed_date`, `adjudication_authority`, `adjudicated_status`, `adjudicated_equivalence_score`, `adjudicator`, `adjudication_timestamp`.

## Evidence and review

One evidence row links one paper, experiment, and claim. `criteria_json` is a JSON object serialized inside a CSV cell, covering every configured criterion. Use the JSON importer to avoid hand-escaping errors. Scores are strings from 0 through 5. Allowed statuses are PRECEDED, PARTIALLY_PRECEDED, ADJACENT, NOT_RELEVANT, and UNCERTAIN.

`AGENT_PROVISIONAL` identifies a proposed judgment. `HUMAN_ADJUDICATED` records a supplied human decision; the software cannot authenticate the reviewer. Original status and score remain intact alongside adjudicated fields. Review history retains the preceding matrix and decision payload.

## Expansion rounds

Stage 1 round IDs use `ROUND-S1-001`; candidate families use `FAM-001`. Record the trigger set prospectively. A coverage row marks backward, forward, author, and terminology paths COMPLETE only when actually completed. Preserve failed retrieval in the ledger. The stopping checker compares declared counts with candidate/evidence/family records and requires two consecutive complete null rounds. Empty trigger sets cannot qualify. This v0.1 stopping checker is intended for Stage 1; evaluate Stage 2 coverage separately.

## Data not frozen automatically

Candidate records, evidence, review histories, raw responses, and the cold-pass corpus are not included in the initial control freeze. Preserve private snapshots when making stage transitions or publishing reports. Files are single-writer CSVs, not a transactional database.
