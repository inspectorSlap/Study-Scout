#!/usr/bin/env python3
"""Create an empty, private study workspace from a JSON specification."""
import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from schemas import SCHEMAS, OPTIONAL_SCHEMAS

SOURCE_FIELDS = ['source_id', 'source_name', 'access_method', 'cold_allowed']
SOURCES = [('S-01', 'OpenAlex'), ('S-02', 'Crossref'), ('S-03', 'Semantic Scholar Graph'), ('S-04', 'arXiv'), ('S-05', 'DBLP')]

def validate_config(config):
    for field in ('study_id', 'title', 'cutoff_date', 'claims', 'criteria'):
        if not config.get(field):
            raise ValueError(f'{field} is required')
    date.fromisoformat(config['cutoff_date'])
    ids = []
    for claim in config['claims']:
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', claim['id']) or not claim['text'].strip():
            raise ValueError('claims need safe IDs and nonempty text')
        ids.append(claim['id'])
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate claim IDs')
    if not isinstance(config['criteria'], dict) or any(not isinstance(v, str) or not v.strip() for v in config['criteria'].values()):
        raise ValueError('criteria must map criterion names to descriptions')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    validate_config(config)
    if args.workspace.exists():
        parser.error('workspace already exists; refusing to overwrite')
    args.workspace.mkdir(parents=True)
    (args.workspace / 'study.json').write_text(json.dumps(config, indent=2) + '\n')
    for relative, fields in {**SCHEMAS, **OPTIONAL_SCHEMAS}.items():
        path = args.workspace / 'data' / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', newline='') as handle:
            csv.writer(handle, lineterminator='\n').writerow(fields)
    control = args.workspace / 'control'
    control.mkdir()
    with (control / 'SOURCE_REGISTER.csv').open('w', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(SOURCE_FIELDS)
        writer.writerows((sid, name, 'API', 'TRUE') for sid, name in SOURCES)
    for directory in ('searches/raw', 'searches/results', 'reviews', 'synthesis'):
        (args.workspace / 'data' / directory).mkdir(parents=True, exist_ok=True)
    print(f'Created {args.workspace}; add seeds, then freeze before retrieval.')

if __name__ == '__main__':
    main()
