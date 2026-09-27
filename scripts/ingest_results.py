#!/usr/bin/env python3
"""Ingest one normalized execution result without erasing duplicate discovery routes."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from pathlib import Path

from rig_common import DATA, append_rows, read_csv


LEDGER = DATA / "searches" / "retrieval-ledger.csv"
QUERIES = DATA / "searches" / "queries.csv"
CANDIDATES = DATA / "corpus" / "candidates.csv"
DISCOVERIES = DATA / "corpus" / "discoveries.csv"
CANDIDATE_FIELDS = ["paper_id", "title", "authors", "year", "venue", "url", "doi", "arxiv_id", "source_found", "stage", "peer_reviewed", "retrieved_date", "verification_state", "disposition", "rejection_reason", "first_seen_round_id", "family_id", "notes"]
DISCOVERY_FIELDS = ["discovery_id", "paper_id", "query_id", "execution_id", "stage", "track", "source", "source_position", "discovered_date", "route_type", "notes"]


def clean(value: str) -> str:
    return " ".join(value.lower().split())


def keys(row: dict[str, str]) -> set[str]:
    result: set[str] = set()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", row.get("doi", "").strip().lower()).rstrip("/.")
    arxiv = re.sub(r"v\d+$", "", row.get("arxiv_id", "").strip().lower())
    if doi:
        result.add("doi:" + doi)
    if arxiv:
        result.add("arxiv:" + arxiv)
    if row.get("title") and re.fullmatch(r"\d{4}", row.get("year", "")):
        result.add(f"title-year:{clean(row['title'])}|{row['year']}")
    return result


def next_number(rows: list[dict[str, str]], field: str, prefix: str) -> int:
    return max((int(row[field].rsplit("-", 1)[1]) for row in rows if row[field].startswith(prefix)), default=0) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--result-file", type=Path)
    parser.add_argument("--round-id", default="")
    args = parser.parse_args()
    ledger = {row["execution_id"]: row for row in read_csv(LEDGER)}
    if args.execution_id not in ledger:
        parser.error("execution must be logged before ingestion")
    execution = ledger[args.execution_id]
    queries = {row["query_id"]: row for row in read_csv(QUERIES)}
    query = queries[execution["query_id"]]
    path = args.result_file or (DATA.parent / execution["normalized_result_paths"])
    if not path.is_absolute():
        path = DATA.parent / path
    if not path.is_file():
        parser.error(f"result file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        results = list(csv.DictReader(handle))

    candidates = read_csv(CANDIDATES)
    discoveries = read_csv(DISCOVERIES)
    known_routes = {(row["execution_id"], row["source_position"]) for row in discoveries}
    key_to_paper: dict[str, str] = {}
    for candidate in candidates:
        for key in keys(candidate):
            key_to_paper[key] = candidate["paper_id"]
    paper_number = next_number(candidates, "paper_id", "P-")
    discovery_number = next_number(discoveries, "discovery_id", "D-")
    today = date.today().isoformat()
    new_candidates: list[dict[str, str]] = []
    new_discoveries: list[dict[str, str]] = []
    for row in results:
        route = (args.execution_id, row["source_position"])
        if route in known_routes:
            continue
        row_keys = keys(row)
        matches = {key_to_paper[key] for key in row_keys if key in key_to_paper}
        if len(matches) > 1:
            raise SystemExit(f"identity collision at source position {row['source_position']}: {sorted(matches)}")
        if matches:
            paper_id = next(iter(matches))
        else:
            paper_id = f"P-{paper_number:06d}"
            paper_number += 1
            candidate = {
                "paper_id": paper_id, "title": row.get("title", ""), "authors": row.get("authors", ""), "year": row.get("year", ""),
                "venue": row.get("venue", ""), "url": row.get("url", ""), "doi": row.get("doi", ""), "arxiv_id": row.get("arxiv_id", ""),
                "source_found": execution["source_name"], "stage": execution["stage"], "peer_reviewed": row.get("peer_reviewed_hint", "UNKNOWN"),
                "retrieved_date": today, "verification_state": "UNVERIFIED", "disposition": "SCREENING", "rejection_reason": "",
                "first_seen_round_id": args.round_id, "family_id": "", "notes": "Metadata ingestion; experimental relevance not yet coded.",
            }
            new_candidates.append(candidate)
            candidates.append(candidate)
            for key in row_keys:
                key_to_paper[key] = paper_id
        new_discoveries.append({
            "discovery_id": f"D-{discovery_number:06d}", "paper_id": paper_id, "query_id": execution["query_id"],
            "execution_id": args.execution_id, "stage": execution["stage"], "track": query["track"], "source": execution["source_name"],
            "source_position": row["source_position"], "discovered_date": today, "route_type": query["query_origin"], "notes": "Route preserved from normalized execution output.",
        })
        known_routes.add(route)
        for key in row_keys:
            key_to_paper[key] = paper_id
        discovery_number += 1
    append_rows(CANDIDATES, CANDIDATE_FIELDS, new_candidates)
    append_rows(DISCOVERIES, DISCOVERY_FIELDS, new_discoveries)
    print(f"Ingested {len(new_discoveries)} route(s); created {len(new_candidates)} candidate(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
