#!/usr/bin/env python3
"""Apply structured human decisions while retaining the original StudyScout proposal."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
import shutil
from pathlib import Path

from rig_common import DATA, STATUSES


MATRIX = DATA / "coding" / "evidence-matrix.csv"
DECISIONS = {"ACCEPT", "LOWER", "RAISE", "CHANGE_STATUS", "NEEDS_SOURCE"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("decisions", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.decisions.read_text(encoding="utf-8"))
    incoming = payload.get("decisions", [])
    if not payload.get("batch_id") or not payload.get("reviewed_date") or not payload.get("adjudication_timestamp"):
        parser.error("batch_id, reviewed_date, and adjudication_timestamp are required")

    date.fromisoformat(payload['reviewed_date'])
    datetime.fromisoformat(payload['adjudication_timestamp'].replace('Z', '+00:00'))
    with MATRIX.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    by_id = {row["evidence_id"]: row for row in rows}
    seen: set[str] = set()
    for item in incoming:
        evidence_id = item.get("evidence_id", "")
        if evidence_id in seen or evidence_id not in by_id:
            parser.error(f"duplicate or unknown evidence ID: {evidence_id}")
        seen.add(evidence_id)
        row = by_id[evidence_id]
        if row["review_batch_id"] != payload["batch_id"] or row["manual_review_required"] != "TRUE":
            parser.error(f"batch or review requirement mismatch: {evidence_id}")
        decision = item.get("decision", "")
        status = item.get("status", "")
        try:
            score = int(item.get("score"))
        except (TypeError, ValueError):
            parser.error(f"invalid score: {evidence_id}")
        if decision not in DECISIONS or status not in STATUSES or not 0 <= score <= 5:
            parser.error(f"invalid decision/status/score: {evidence_id}")
        if not item.get("reason") or not item.get("adjudicator"):
            parser.error(f"reason and adjudicator required: {evidence_id}")
        if decision == "ACCEPT" and (status != row["status"] or str(score) != row["equivalence_score"]):
            parser.error(f"ACCEPT must match the proposal: {evidence_id}")

    history = DATA / 'reviews' / 'history'
    history.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    shutil.copyfile(MATRIX, history / f'{stamp}-before.csv')
    (history / f'{stamp}-decisions.json').write_text(json.dumps(payload, indent=2) + '\n')
    for item in incoming:
        row = by_id[item["evidence_id"]]
        needs_source = item["decision"] == "NEEDS_SOURCE" or bool(item.get("additional_source_needed"))
        row.update({
            "manual_review_status": "NEEDS_SOURCE" if needs_source else ("ACCEPTED" if item["decision"] == "ACCEPT" else "REVISED"),
            "reviewer_decision": item["decision"],
            "reviewer_notes": item["reason"],
            "reviewed_date": payload["reviewed_date"],
            "adjudication_authority": "AGENT_PROVISIONAL" if needs_source else "HUMAN_ADJUDICATED",
            "adjudicated_status": "" if needs_source else item["status"],
            "adjudicated_equivalence_score": "" if needs_source else str(item["score"]),
            "adjudicator": "" if needs_source else item["adjudicator"],
            "adjudication_timestamp": "" if needs_source else payload["adjudication_timestamp"],
        })
    with MATRIX.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Applied {len(incoming)} human decision(s) from {args.decisions}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
