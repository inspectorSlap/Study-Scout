#!/usr/bin/env python3
"""Verify and replay a bundled real-study snapshot without network access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def verify(case):
    manifest = json.loads((case / 'MANIFEST.json').read_text(encoding='utf-8'))
    base = case.resolve()
    for relative, digest in manifest['sha256'].items():
        path = (case / relative).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise ValueError(f'missing or unsafe manifest path: {relative}')
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'case artifact changed: {relative}')
    actual = {p.relative_to(case).as_posix() for p in (case / 'snapshot').rglob('*') if p.is_file()}
    if not actual.issubset(manifest['sha256']):
        raise ValueError('snapshot contains unmanifested files')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    case = args.case.resolve()
    manifest = verify(case)
    if args.workspace.exists():
        parser.error('workspace already exists; refusing to overwrite')
    shutil.copytree(case / 'snapshot', args.workspace)
    env = dict(os.environ, STUDYSCOUT_WORKSPACE=str(args.workspace.resolve()), PYTHONDONTWRITEBYTECODE='1')
    for script, options in [('release_guard', []), ('validate_records', []),
                            ('build_matrix', ['--output', 'data/synthesis/matrix.md']),
                            ('check_stopping_rule', ['--write-status', 'synthesis/stopping.md'])]:
        subprocess.run([sys.executable, str(ROOT / 'scripts' / (script + '.py')), *options], env=env, check=True)
    for relative in manifest['reproduced_outputs']:
        if (args.workspace / relative).read_bytes() != (case / 'snapshot' / relative).read_bytes():
            raise SystemExit(f'Regenerated output differs: {relative}')
    print('Verified snapshot and reproduced outputs byte-for-byte. No network requests were made.')
    print('This replays recorded evidence; it does not repeat the literature search or adjudicate findings.')

if __name__ == '__main__':
    main()
