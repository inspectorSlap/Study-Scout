#!/usr/bin/env python3
"""Render a non-mutating human-review batch for mandatory StudyScout adjudication."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from rig_common import DATA, ROOT, read_csv


def show(value: str) -> str:
    return value.strip() or "_Not recorded_"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"BATCH-\d{3}", args.batch_id) or args.limit < 1:
        parser.error("invalid batch ID or limit")
    rows = [
        row for row in read_csv(DATA / "coding" / "evidence-matrix.csv")
        if row["manual_review_required"] == "TRUE" and row["manual_review_status"] in {"PENDING", "NEEDS_SOURCE"} and not row["review_batch_id"]
    ]
    rows.sort(key=lambda row: (-int(row["equivalence_score"]), row["claim_id"], row["paper_id"], row["evidence_id"]))
    rows = rows[:args.limit]
    lines = [f"# Human Review {args.batch_id}", "", f"Items: **{len(rows)}**", ""]
    for number, row in enumerate(rows, start=1):
        lines.extend([
            f"## {number}. {row['evidence_id']} — {show(row['title'])}", "",
            f"- Paper / claim / experiment: `{row['paper_id']}` / `{row['claim_id']}` / `{row['experiment_id']}`",
            f"- Provisional: **{row['status']}**, equivalence **{row['equivalence_score']}/5**",
            f"- Review focus: {'close test without a precedence finding; check outcome and implementation differences' if int(row['equivalence_score']) >= 4 and row['status'] not in {'PRECEDED', 'PARTIALLY_PRECEDED'} else 'proposed precedence; check the claimed correspondence and missing criteria'}",
            f"- Primary-source state: `{row['verification_state']}`",
            f"- Inspected source/version: {show(row['primary_source'])} (candidate metadata year: {show(row['year'])})",
            f"- Evidence location: {show(row['evidence_location'])}",
            f"- Evidence excerpt: {show(row['evidence_quote'])}",
            f"- Manipulation: {show(row['manipulation'])}",
            f"- Comparison: {show(row['comparison'])}",
            f"- Held constants: {show(row['held_constants'])}",
            f"- Observable: {show(row['observable'])}",
            f"- Coder inference: {show(row['coder_inference'])}",
            f"- Uncertainty or missing element: {show(row['uncertainty'])}", "",
            "### Reviewer response", "", "- Decision:", "- Replacement score:", "- Replacement status:", "- Reason:", "- Additional source needed:", "- Adjudicator name:", "",
        ])
    if not rows:
        lines.extend(["No unbatched mandatory-review items are pending.", ""])
    output = args.output or Path("data/reviews") / f"{args.batch_id}.md"
    output = output if output.is_absolute() else ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
