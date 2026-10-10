#!/usr/bin/env python3
"""Render a deterministic StudyScout paper-by-claim matrix from evidence records."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from rig_common import CLAIM_IDS, DATA, ROOT, effective_judgment, read_csv
from report_scope import scope_lines


ORDER = {"PRECEDED": 5, "PARTIALLY_PRECEDED": 4, "ADJACENT": 3, "UNCERTAIN": 2, "NOT_RELEVANT": 1}


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def rank(row):
    score, status = effective_judgment(row)
    return score, ORDER[status], row['evidence_id']


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()
    if args.output and args.stdout:
        parser.error("choose --output or --stdout")

    evidence = read_csv(DATA / "coding" / "evidence-matrix.csv")
    candidates = {row["paper_id"]: row for row in read_csv(DATA / "corpus" / "candidates.csv")}
    cells: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in evidence:
        cells[(row["paper_id"], row["claim_id"])].append(row)
    paper_ids = sorted({row["paper_id"] for row in evidence})
    lines = [
        "# StudyScout Cross-Claim Matrix", "",
        "Each cell shows the highest-equivalence evidence record. Mandatory judgments remain provisional until human adjudication.", "",
        *scope_lines(list(candidates.values()), evidence),
        "| Paper | " + " | ".join(CLAIM_IDS) + " |",
        "|---|" + "---|" * len(CLAIM_IDS),
    ]
    for paper_id in paper_ids:
        candidate = candidates.get(paper_id, {})
        title = candidate.get("title") or next(row["title"] for row in evidence if row["paper_id"] == paper_id)
        rendered = []
        for claim_id in CLAIM_IDS:
            rows = cells.get((paper_id, claim_id), [])
            if not rows:
                rendered.append("—")
                continue
            rows.sort(key=rank, reverse=True)
            best = rows[0]
            if best["adjudication_authority"] == "HUMAN_ADJUDICATED":
                cell = f"{best['adjudicated_status']} ({best['adjudicated_equivalence_score']}) [HUMAN]"
            elif best["manual_review_required"] == "TRUE":
                cell = f"PROVISIONAL {best['status']} ({best['equivalence_score']})"
            else:
                cell = f"{best['status']} ({best['equivalence_score']})"
            rendered.append(cell + (f" ×{len(rows)}" if len(rows) > 1 else ""))
        lines.append(f"| {paper_id} — {escape(title)} | " + " | ".join(rendered) + " |")
    if not paper_ids:
        lines.append("| _No evidence coded_ | " + " | ".join("—" for _ in CLAIM_IDS) + " |")
    lines.append("")
    text = "\n".join(lines)
    if args.stdout or not args.output:
        print(text, end="")
        return 0
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
