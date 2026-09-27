#!/usr/bin/env python3
"""Verify frozen study specification, source policy, and seed query bytes."""
import json
from rig_common import ROOT, CONTROL, DATA, sha256, read_csv

ARTIFACTS = ('study.json', 'control/SOURCE_REGISTER.csv', 'data/searches/seed-queries.csv')

def sealed():
    manifest = CONTROL / 'freeze.json'
    if not manifest.is_file():
        return False, ['study is not frozen; run freeze_study.py']
    try:
        record = json.loads(manifest.read_text())
        if set(record['sha256']) != set(ARTIFACTS):
            return False, ['freeze manifest has the wrong artifact set']
        errors = [f'changed or missing frozen artifact: {name}' for name in ARTIFACTS
                  if not (ROOT / name).is_file() or sha256(ROOT / name) != record['sha256'][name]]
        if not read_csv(DATA / 'searches/seed-queries.csv'):
            errors.append('seed registry is empty')
        return not errors, errors
    except (ValueError, KeyError, TypeError, OSError) as exc:
        return False, [f'invalid freeze record: {type(exc).__name__}']

def require_release():
    good, errors = sealed()
    if not good:
        raise SystemExit('STUDY BLOCKED:\n- ' + '\n- '.join(errors))

if __name__ == '__main__':
    require_release()
    print('Frozen study controls verified')
