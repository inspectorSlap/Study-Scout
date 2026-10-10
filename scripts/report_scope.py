"""Summarize recorded search bounds beside generated study results."""

from collections import Counter

from rig_common import DATA, read_csv


TERMINAL_LABELS = {
    "SOURCE_EXHAUSTED": "source exhausted",
    "QUERY_COVERAGE_COMPLETE": "query coverage complete",
    "PAGE_LIMIT_REACHED": "page limit reached",
    "API_RESULT_CAP": "API result cap",
    "API_TRUNCATED": "API truncated",
    "API_FAILURE": "API failure",
    "RATE_LIMITED": "rate limited",
    "ACCESS_BLOCKED": "access blocked",
    "MANUAL_STOP": "manual stop",
    "PENDING": "pending",
}


def scope_lines(candidates=None, evidence=None):
    candidates = candidates if candidates is not None else read_csv(DATA / "corpus/candidates.csv")
    evidence = evidence if evidence is not None else read_csv(DATA / "coding/evidence-matrix.csv")
    ledger = read_csv(DATA / "searches/retrieval-ledger.csv")
    dispositions = Counter(row["disposition"] or "UNSCREENED" for row in candidates)
    terminals = Counter(row["terminal_condition"] for row in ledger)
    pending_review = sum(
        row["manual_review_required"] == "TRUE" and row["manual_review_status"] in {"PENDING", "NEEDS_SOURCE"}
        for row in evidence
    )
    disposition_text = ", ".join(
        f"{count} {name.lower().replace('_', ' ')}"
        for name, count in sorted(dispositions.items())
    ) or "none"
    terminal_text = ", ".join(
        f"{count} {TERMINAL_LABELS.get(name, name.lower().replace('_', ' '))}"
        for name, count in sorted(terminals.items(), key=lambda item: (-item[1], item[0]))
    ) or "none"
    return [
        "## Recorded scope and unresolved work", "",
        f"- Candidate records: **{len(candidates)}** ({disposition_text}).",
        f"- Evidence records: **{len(evidence)}**; pending mandatory human reviews: **{pending_review}**.",
        f"- Retrieval executions: **{len(ledger)}** ({terminal_text}).", "",
        "These counts describe recorded work, not search recall or completeness. Provider result totals may overlap and are not added together. Inspect `data/searches/retrieval-ledger.csv` and unresolved candidates before making a broader claim.", "",
    ]
