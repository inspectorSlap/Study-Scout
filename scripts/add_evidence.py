#!/usr/bin/env python3
"""Append an agent-proposed evidence record from JSON, deriving review requirements."""
import argparse
import json
import re
from datetime import date
from pathlib import Path
from rig_common import CONFIG, CLAIM_IDS, DATA, STATUSES, append_rows, read_csv
from schemas import SCHEMAS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    incoming = json.loads(args.record.read_text())
    path = DATA / 'coding/evidence-matrix.csv'
    fields = SCHEMAS['coding/evidence-matrix.csv']
    if set(incoming) - set(fields):
        parser.error('unknown evidence fields')
    row = dict.fromkeys(fields, '')
    row.update(incoming)
    if any(not isinstance(v, str) for v in row.values()):
        parser.error('CSV record values must be strings, including criteria_json')
    if not re.fullmatch(r'EV-\d{6}', row['evidence_id']) or row['evidence_id'] in {r['evidence_id'] for r in read_csv(path)}:
        parser.error('invalid or duplicate evidence ID')
    papers = {r['paper_id']: r for r in read_csv(DATA / 'corpus/candidates.csv')}
    if row['paper_id'] not in papers or row['claim_id'] not in CLAIM_IDS:
        parser.error('unknown paper or claim')
    if row['status'] not in STATUSES or row['equivalence_score'] not in tuple(map(str, range(6))):
        parser.error('invalid status or score')
    try:
        criteria = json.loads(row['criteria_json'])
        if not isinstance(criteria, dict) or set(criteria) != set(CONFIG['criteria']):
            parser.error('criteria_json must cover configured criteria exactly')
    except ValueError:
        parser.error('criteria_json is not valid JSON')
    for field in ('experiment_id', 'evidence_location', 'coder_inference', 'verification_state'):
        if not row[field]:
            parser.error(f'{field} is required')
    for field in ('reviewer_decision','reviewer_notes','reviewed_date','adjudicated_status','adjudicated_equivalence_score','adjudicator','adjudication_timestamp','review_batch_id'):
        if row[field]:
            parser.error('new proposals cannot contain review decisions')
    paper = papers[row['paper_id']]
    for field in ('title','authors','year','venue','url','doi','source_found','stage'):
        row[field] = paper[field]
    required = int(row['equivalence_score']) >= 4 or row['status'] == 'PRECEDED'
    row.update(manual_review_required='TRUE' if required else 'FALSE',
               manual_review_status='PENDING' if required else 'NOT_REQUIRED',
               adjudication_authority='AGENT_PROVISIONAL', retrieved_date=date.today().isoformat())
    append_rows(path, fields, [row])
    print(f"Added {row['evidence_id']}; human review required: {required}")

if __name__ == '__main__':
    main()
