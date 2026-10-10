#!/usr/bin/env python3
"""Hash or verify a completed study workspace without changing its research records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rig_common import ROOT


def files_in_workspace(manifest_path: Path) -> dict[str, Path]:
    files = {}
    for path in ROOT.rglob("*"):
        if ".git" in path.relative_to(ROOT).parts:
            continue
        if path.is_symlink():
            raise ValueError(f"workspace contains a symlink: {path.relative_to(ROOT)}")
        if path.is_file() and path.resolve() != manifest_path:
            files[path.relative_to(ROOT).as_posix()] = path
    return files


def verify(manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != 1 or not isinstance(manifest.get("sha256"), dict):
        raise ValueError("invalid study seal")
    files = files_in_workspace(manifest_path)
    if set(files) != set(manifest["sha256"]):
        raise ValueError("workspace file set differs from the seal")
    for relative, expected in manifest["sha256"].items():
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or path != files[relative].resolve():
            raise ValueError(f"unsafe seal path: {relative}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"study artifact changed: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "control/report-seal.json")
    parser.add_argument("--verify", action="store_true", help="Check the seal and the full workspace file set")
    args = parser.parse_args()
    manifest_path = (args.output if args.output.is_absolute() else ROOT / args.output).resolve()
    if args.verify:
        verify(manifest_path)
        print(f"Verified study seal: {len(files_in_workspace(manifest_path))} files")
        return 0
    if manifest_path.exists():
        parser.error("seal already exists; preserve it and use a new path for a later snapshot")
    from release_guard import sealed
    from validate_records import validate
    good, freeze_errors = sealed()
    errors = freeze_errors + validate()
    if not good or errors:
        parser.error("workspace is not ready to seal: " + "; ".join(dict.fromkeys(errors)))
    files = files_in_workspace(manifest_path)
    manifest = {
        "version": 1,
        "description": "Workspace byte-consistency seal; not independent proof of research authenticity.",
        "sha256": {relative: hashlib.sha256(path.read_bytes()).hexdigest() for relative, path in sorted(files.items())},
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Sealed {len(files)} files at {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
