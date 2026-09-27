#!/usr/bin/env python3
"""Append one immutable StudyScout source-execution record, including failures and zero results."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone

from rig_common import DATA, CONTROL, TERMINALS, append_rows, read_csv


QUERIES = DATA / "searches" / "queries.csv"
LEDGER = DATA / "searches" / "retrieval-ledger.csv"
SOURCES = CONTROL / "SOURCE_REGISTER.csv"
FIELDS = [
    "execution_id", "query_id", "stage", "source_id", "source_name", "access_method",
    "parameters_json", "filters", "run_started_at", "run_completed_at",
    "requested_page_size", "pagination_start", "pagination_end", "pages_retrieved",
    "result_count", "results_available", "serious_candidate_count", "api_failure",
    "api_truncated", "terminal_condition", "status", "raw_response_paths",
    "normalized_result_paths", "notes",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-id", required=True)
    parser.add_argument("--query-id", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--parameters-json", default="{}")
    parser.add_argument("--filters", default="")
    parser.add_argument("--started-at", default="")
    parser.add_argument("--completed-at", default="")
    parser.add_argument("--page-size", type=int, default=0)
    parser.add_argument("--pagination-start", default="")
    parser.add_argument("--pagination-end", default="")
    parser.add_argument("--pages", type=int, required=True)
    parser.add_argument("--result-count", type=int, required=True)
    parser.add_argument("--results-available", type=int)
    parser.add_argument("--serious-candidates", type=int, default=0)
    parser.add_argument("--api-failure", choices=["TRUE", "FALSE"], default="FALSE")
    parser.add_argument("--api-truncated", choices=["TRUE", "FALSE"], default="FALSE")
    parser.add_argument("--terminal", choices=sorted(TERMINALS), required=True)
    parser.add_argument("--status", choices=["COMPLETE", "FAILED", "BLOCKED"], required=True)
    parser.add_argument("--raw-paths", default="")
    parser.add_argument("--normalized-paths", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    if not re.fullmatch(r"R-S[12]-\d{6}", args.execution_id):
        parser.error("execution ID must match R-S1-000001 or R-S2-000001")
    try:
        parameters = json.loads(args.parameters_json)
    except json.JSONDecodeError as exc:
        parser.error(f"invalid parameters JSON: {exc}")
    if not isinstance(parameters, dict):
        parser.error("parameters JSON must be an object")
    values = (args.page_size, args.pages, args.result_count, args.serious_candidates)
    if min(values) < 0 or (args.results_available is not None and args.results_available < 0):
        parser.error("counts cannot be negative")

    queries = {row["query_id"]: row for row in read_csv(QUERIES)}
    sources = {row["source_id"]: row for row in read_csv(SOURCES)}
    if args.query_id not in queries:
        parser.error(f"unknown query: {args.query_id}")
    if args.source_id not in sources:
        parser.error(f"unknown source: {args.source_id}")
    if args.execution_id in {row["execution_id"] for row in read_csv(LEDGER)}:
        parser.error(f"execution ID already exists: {args.execution_id}")
    query = queries[args.query_id]
    expected = "1" if query["stage"] == "STAGE_1_COLD" else "2"
    if not args.execution_id.startswith(f"R-S{expected}-"):
        parser.error("execution stage does not match query stage")

    source = sources[args.source_id]
    completed = args.completed_at or now()
    append_rows(LEDGER, FIELDS, [{
        "execution_id": args.execution_id,
        "query_id": args.query_id,
        "stage": query["stage"],
        "source_id": source["source_id"],
        "source_name": source["source_name"],
        "access_method": source["access_method"],
        "parameters_json": json.dumps(parameters, sort_keys=True, separators=(",", ":")),
        "filters": args.filters,
        "run_started_at": args.started_at or completed,
        "run_completed_at": completed,
        "requested_page_size": str(args.page_size),
        "pagination_start": args.pagination_start,
        "pagination_end": args.pagination_end,
        "pages_retrieved": str(args.pages),
        "result_count": str(args.result_count),
        "results_available": "" if args.results_available is None else str(args.results_available),
        "serious_candidate_count": str(args.serious_candidates),
        "api_failure": args.api_failure,
        "api_truncated": args.api_truncated,
        "terminal_condition": args.terminal,
        "status": args.status,
        "raw_response_paths": args.raw_paths,
        "normalized_result_paths": args.normalized_paths,
        "notes": args.notes,
    }])
    print(f"Logged {args.execution_id}: terminal={args.terminal}, results={args.result_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
