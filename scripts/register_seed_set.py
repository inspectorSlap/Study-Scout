#!/usr/bin/env python3
"""Register the checksum-frozen StudyScout seeds with deterministic Stage 1 query IDs."""

from __future__ import annotations

import re

from rig_common import CLAIM_IDS, DATA, append_rows, read_csv, split_claim_ids


SEEDS = DATA / "searches" / "seed-queries.csv"
QUERIES = DATA / "searches" / "queries.csv"
FIELDS = [
    "query_id", "stage", "query_origin", "seed_id", "parent_query_id",
    "parent_paper_id", "parent_edge_id", "expansion_round_id", "generation",
    "track", "claim_ids", "query_text", "created_date", "created_by", "notes",
]


def main() -> int:
    from release_guard import require_release
    require_release()
    seeds = read_csv(SEEDS)
    existing = read_csv(QUERIES)
    by_seed = {row["seed_id"]: row for row in existing if row["seed_id"]}
    used_queries = {row["query_id"] for row in existing}
    additions: list[dict[str, str]] = []
    for number, seed in enumerate(seeds, start=1):
        if not re.fullmatch(r"SQ-\d{3}", seed["seed_id"]):
            raise SystemExit(f"invalid seed ID: {seed['seed_id']}")
        if seed["ordinal"] != str(number):
            raise SystemExit(f"seed ordinal is not contiguous at {seed['seed_id']}")
        claims = split_claim_ids(seed["claim_ids"])
        if not claims or not claims.issubset(CLAIM_IDS):
            raise SystemExit(f"invalid claim mapping: {seed['seed_id']}")
        if not seed["query_text"].strip() or not seed["track"].strip() or not seed["freeze_date"].strip():
            raise SystemExit(f"incomplete frozen seed: {seed['seed_id']}")
        query_id = f"Q-S1-{number:06d}"
        if seed["seed_id"] in by_seed:
            current = by_seed[seed["seed_id"]]
            if current["query_id"] != query_id or any(current[field] != seed[field] for field in ("track", "claim_ids", "query_text")):
                raise SystemExit(f"frozen seed registration conflict: {seed['seed_id']}")
            continue
        if query_id in used_queries:
            raise SystemExit(f"query ID already belongs to another record: {query_id}")
        additions.append({
            "query_id": query_id,
            "stage": "STAGE_1_COLD",
            "query_origin": "SEED",
            "seed_id": seed["seed_id"],
            "parent_query_id": "",
            "parent_paper_id": "",
            "parent_edge_id": "",
            "expansion_round_id": "",
            "generation": "0",
            "track": seed["track"],
            "claim_ids": seed["claim_ids"],
            "query_text": seed["query_text"],
            "created_date": seed["freeze_date"],
            "created_by": "FROZEN_SEED_IMPORT",
            "notes": "Exact copy of the checksum-frozen StudyScout seed.",
        })
    append_rows(QUERIES, FIELDS, additions)
    print(f"Registered {len(additions)} seed queries; {len(seeds) - len(additions)} already present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
