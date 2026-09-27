#!/usr/bin/env python3
"""Shared constants and read-only helpers for the StudyScout rig."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path


ROOT = Path(os.environ.get("STUDYSCOUT_WORKSPACE", Path(__file__).resolve().parents[1] / "workspace")).resolve()
CONTROL = ROOT / "control"
DATA = ROOT / "data"

def load_config():
    path = ROOT / "study.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

CONFIG = load_config()
CLAIM_IDS = tuple(item["id"] for item in CONFIG.get("claims", []))
STATUSES = {
    "PRECEDED",
    "PARTIALLY_PRECEDED",
    "ADJACENT",
    "NOT_RELEVANT",
    "UNCERTAIN",
}
STAGES = {"STAGE_1_COLD", "STAGE_2_INJECTED", "STAGE_2_DESCENDANT"}
QUERY_ORIGINS = {
    "SEED",
    "DISCOVERED",
    "CITATION",
    "AUTHOR",
    "TERMINOLOGY",
    "EXPERIMENTAL_SHAPE",
    "CONJUNCTION",
    "INJECTED",
}
TERMINALS = {
    "SOURCE_EXHAUSTED",
    "QUERY_COVERAGE_COMPLETE",
    "PAGE_LIMIT_REACHED",
    "API_RESULT_CAP",
    "API_TRUNCATED",
    "API_FAILURE",
    "RATE_LIMITED",
    "ACCESS_BLOCKED",
    "MANUAL_STOP",
    "PENDING",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def append_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    if header(path) != fields:
        raise ValueError(f"schema mismatch: {path.relative_to(ROOT)}")
    with path.open("a", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=fields, lineterminator="\n").writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_claim_ids(value: str) -> set[str]:
    return {item.strip() for item in value.replace("|", ";").split(";") if item.strip()}
