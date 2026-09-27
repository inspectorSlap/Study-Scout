#!/usr/bin/env python3
"""Assign unbatched mandatory StudyScout evidence rows to one stable human-review batch."""

from __future__ import annotations

import argparse
import csv
import re

from rig_common import DATA


MATRIX = DATA / "coding" / "evidence-matrix.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--evidence-id", action="append", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"BATCH-\d{3}", args.batch_id):
        parser.error("invalid batch ID")
    if len(args.evidence_id) != len(set(args.evidence_id)):
        parser.error("duplicate evidence ID")

    with MATRIX.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    by_id = {row["evidence_id"]: row for row in rows}
    for evidence_id in args.evidence_id:
        row = by_id.get(evidence_id)
        if not row:
            parser.error(f"unknown evidence ID: {evidence_id}")
        if row["manual_review_required"] != "TRUE" or row["manual_review_status"] not in {"PENDING", "NEEDS_SOURCE"}:
            parser.error(f"not pending mandatory review: {evidence_id}")
        if row["review_batch_id"]:
            parser.error(f"already batched: {evidence_id}")
    for evidence_id in args.evidence_id:
        by_id[evidence_id]["review_batch_id"] = args.batch_id
    with MATRIX.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Assigned {len(args.evidence_id)} item(s) to {args.batch_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
