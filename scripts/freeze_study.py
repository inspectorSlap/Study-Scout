#!/usr/bin/env python3
"""Freeze controls once, after validation. Revisions require a new workspace."""
import json
from datetime import datetime, timezone
from rig_common import ROOT, CONTROL, DATA, sha256, read_csv
from release_guard import ARTIFACTS
from validate_records import validate


def main():
    errors = validate()
    if errors:
        raise SystemExit('\n'.join(errors))
    if not read_csv(DATA / 'searches/seed-queries.csv'):
        raise SystemExit('Add at least one seed before freezing')
    record = {'version': 1, 'frozen_at': datetime.now(timezone.utc).isoformat(),
              'sha256': {name: sha256(ROOT / name) for name in ARTIFACTS}}
    with (CONTROL / 'freeze.json').open('x') as handle:
        json.dump(record, handle, indent=2)
        handle.write('\n')
    print('Study frozen. Keep this manifest with your research record.')

if __name__ == '__main__':
    main()
