#!/usr/bin/env python3
"""Append one StudyScout query and its complete one-to-many genealogy."""

from __future__ import annotations

import argparse
import re
from datetime import date

from rig_common import CLAIM_IDS, DATA, QUERY_ORIGINS, STAGES, append_rows, read_csv, split_claim_ids


QUERIES = DATA / "searches" / "queries.csv"
SEEDS = DATA / "searches" / "seed-queries.csv"
PARENTS = DATA / "searches" / "query-parents.csv"
QUERY_FIELDS = [
    "query_id", "stage", "query_origin", "seed_id", "parent_query_id",
    "parent_paper_id", "parent_edge_id", "expansion_round_id", "generation",
    "track", "claim_ids", "query_text", "created_date", "created_by", "notes",
]
PARENT_FIELDS = ["parent_link_id", "query_id", "parent_type", "parent_id", "relation", "round_id", "created_date", "notes"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--origin", required=True, choices=sorted(QUERY_ORIGINS))
    parser.add_argument("--stage", choices=sorted(STAGES), default="STAGE_1_COLD")
    parser.add_argument("--seed-id", default="")
    parser.add_argument("--query", default="")
    parser.add_argument("--track", default="")
    parser.add_argument("--claims", default="")
    parser.add_argument("--parent-query-id", action="append", default=[])
    parser.add_argument("--parent-paper-id", action="append", default=[])
    parser.add_argument("--parent-edge-id", action="append", default=[])
    parser.add_argument("--expansion-round-id", default="")
    parser.add_argument("--generation", type=int)
    parser.add_argument("--created-by", default="AGENT")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    stage_number = "1" if args.stage == "STAGE_1_COLD" else "2"
    if not re.fullmatch(fr"Q-S{stage_number}-\d{{6}}", args.query_id):
        parser.error("query ID does not match its stage")
    if args.query_id in {row["query_id"] for row in read_csv(QUERIES)}:
        parser.error(f"query ID already exists: {args.query_id}")

    parent_values = [("QUERY", item) for item in args.parent_query_id]
    parent_values += [("PAPER", item) for item in args.parent_paper_id]
    parent_values += [("EDGE", item) for item in args.parent_edge_id]
    if args.origin == "SEED":
        if not args.seed_id or args.query or args.track or args.claims or parent_values:
            parser.error("SEED requires only --seed-id and copies frozen values")
        seeds = {row["seed_id"]: row for row in read_csv(SEEDS)}
        if args.seed_id not in seeds:
            parser.error(f"unknown seed ID: {args.seed_id}")
        seed = seeds[args.seed_id]
        query, track, claims, generation = seed["query_text"], seed["track"], seed["claim_ids"], 0
    else:
        if args.seed_id or not args.query.strip() or not args.track.strip() or not args.claims.strip():
            parser.error("derived queries require --query, --track, and --claims, and no seed ID")
        if not parent_values:
            parser.error("derived queries require at least one recorded parent")
        if args.generation is None or args.generation < 1:
            parser.error("derived queries require --generation >= 1")
        if args.origin == "INJECTED" and args.stage == "STAGE_1_COLD":
            parser.error("injected queries cannot enter Stage 1")
        if not split_claim_ids(args.claims).issubset(CLAIM_IDS):
            parser.error("unknown claim ID in --claims")
        query, track, claims, generation = args.query, args.track, args.claims, args.generation

    today = date.today().isoformat()
    first = lambda values: values[0] if values else ""
    row = {
        "query_id": args.query_id,
        "stage": args.stage,
        "query_origin": args.origin,
        "seed_id": args.seed_id,
        "parent_query_id": first(args.parent_query_id),
        "parent_paper_id": first(args.parent_paper_id),
        "parent_edge_id": first(args.parent_edge_id),
        "expansion_round_id": args.expansion_round_id,
        "generation": str(generation),
        "track": track,
        "claim_ids": claims,
        "query_text": query,
        "created_date": today,
        "created_by": args.created_by,
        "notes": args.notes,
    }
    existing_parents = read_csv(PARENTS)
    marker = f"QP-S{stage_number}-"
    next_number = max((int(item["parent_link_id"].rsplit("-", 1)[1]) for item in existing_parents if item["parent_link_id"].startswith(marker)), default=0) + 1
    parent_rows = []
    for parent_type, parent_id in parent_values:
        parent_rows.append({
            "parent_link_id": f"{marker}{next_number:06d}",
            "query_id": args.query_id,
            "parent_type": parent_type,
            "parent_id": parent_id,
            "relation": "DERIVED_FROM",
            "round_id": args.expansion_round_id,
            "created_date": today,
            "notes": args.notes,
        })
        next_number += 1
    append_rows(QUERIES, QUERY_FIELDS, [row])
    append_rows(PARENTS, PARENT_FIELDS, parent_rows)
    print(f"Registered {args.query_id} with {len(parent_rows)} parent link(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
