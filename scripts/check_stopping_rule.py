#!/usr/bin/env python3
"""Recompute StudyScout round completeness, machine-null status, and stop eligibility."""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from rig_common import DATA, read_csv
from report_scope import scope_lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-status", type=Path, help="Optional output; omitted for read-only validation")
    args = parser.parse_args()

    rounds = read_csv(DATA / "searches" / "expansion-rounds.csv")
    coverage = read_csv(DATA / "searches" / "expansion-coverage.csv")
    triggers = read_csv(DATA / "searches" / "round-triggers.csv")
    candidates = read_csv(DATA / "corpus" / "candidates.csv")
    families = {row["family_id"]: row for row in read_csv(DATA / "corpus" / "candidate-families.csv")}
    evidence = read_csv(DATA / "coding" / "evidence-matrix.csv")

    errors: list[str] = []
    max_score: dict[str, int] = defaultdict(lambda: -1)
    for row in evidence:
        max_score[row["paper_id"]] = max(max_score[row["paper_id"]], int(row["equivalence_score"]))

    triggers_by_round: dict[str, set[str]] = defaultdict(set)
    for row in triggers:
        triggers_by_round[row["round_id"]].add(row["paper_id"])
    coverage_by_round: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in coverage:
        coverage_by_round[row["round_id"]][row["paper_id"]] = row

    computed: list[dict[str, object]] = []
    for round_row in sorted(rounds, key=lambda row: int(row["ordinal"])):
        round_id = round_row["round_id"]
        expected = triggers_by_round[round_id]
        actual = coverage_by_round[round_id]
        paths_complete = bool(expected) and set(actual) == expected
        for paper_id in expected:
            record = actual.get(paper_id)
            if not record or any(record[field] != "COMPLETE" for field in ("backward_status", "forward_status", "author_status", "terminology_status")):
                paths_complete = False
        complete = bool(round_row["completed_at"]) and paths_complete
        new_candidates = [row for row in candidates if row["first_seen_round_id"] == round_id]
        ge4 = [row for row in new_candidates if max_score[row["paper_id"]] >= 4]
        productive = {
            row["family_id"] for row in new_candidates
            if row["family_id"] and row["family_id"] in families
            and families[row["family_id"]]["first_seen_round_id"] == round_id
            and max_score[row["paper_id"]] >= 3
        }
        machine_null = complete and not ge4 and not productive
        declared = {
            "trigger_paper_count": len(expected),
            "new_candidates_count": len(new_candidates),
            "new_provisional_ge4_count": len(ge4),
            "new_productive_family_count": len(productive),
            "complete": "TRUE" if complete else "FALSE",
            "machine_null": "TRUE" if machine_null else "FALSE",
        }
        for field, value in declared.items():
            if round_row[field] != str(value):
                errors.append(f"{round_id}: declared {field}={round_row[field]!r}, computed {value!r}")
        computed.append({"id": round_id, "ordinal": int(round_row["ordinal"]), "complete": complete, "null": machine_null})

    last_two = computed[-2:]
    satisfied = (
        len(last_two) == 2
        and last_two[1]["ordinal"] == last_two[0]["ordinal"] + 1
        and all(item["complete"] and item["null"] for item in last_two)
    )
    lines = [
        "# StudyScout Computational Stopping Status",
        "",
        f"Status: **{'SATISFIED' if satisfied else 'NOT SATISFIED'}**",
        "",
        *scope_lines(candidates, evidence),
        "| Round | Complete | Machine-null |",
        "|---|---:|---:|",
    ]
    if computed:
        for item in computed:
            lines.append(f"| {item['id']} | {'TRUE' if item['complete'] else 'FALSE'} | {'TRUE' if item['null'] else 'FALSE'} |")
    else:
        lines.append("| _No rounds recorded_ | FALSE | FALSE |")
    lines.extend(["", "Pending review or blocked source paths remain separate limitations.", ""])
    if args.write_status:
        output = args.write_status if args.write_status.is_absolute() else DATA / args.write_status
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("\n".join(lines), encoding="utf-8")
    if errors:
        print(f"STOPPING-RULE VALIDATION FAILED ({len(errors)} error(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"STOPPING CONDITION {'SATISFIED' if satisfied else 'NOT SATISFIED'}; checked {len(computed)} round(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
