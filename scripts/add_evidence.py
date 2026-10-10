#!/usr/bin/env python3
"""Append an agent-proposed evidence record from JSON, deriving review requirements."""
import argparse
import json
import re
from datetime import date
from pathlib import Path
from rig_common import CONFIG, CLAIM_IDS, DATA, STATUSES, append_rows, read_csv, review_required
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
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', row['experiment_id']):
        parser.error('experiment_id must be a stable nonempty label without spaces')
    if any((old['paper_id'], old['experiment_id'], old['claim_id']) == (row['paper_id'], row['experiment_id'], row['claim_id']) for old in read_csv(path)):
        parser.error('duplicate paper/experiment/claim evidence')
    if row['status'] not in STATUSES or row['equivalence_score'] not in tuple(map(str, range(6))):
        parser.error('invalid status or score')
    try:
        criteria = json.loads(row['criteria_json'])
        if not isinstance(criteria, dict) or set(criteria) != set(CONFIG['criteria']):
            parser.error('criteria_json must cover configured criteria exactly')
        if any(not isinstance(value, str) or not value.strip() for value in criteria.values()):
            parser.error('criteria_json values must be nonempty text')
    except ValueError:
        parser.error('criteria_json is not valid JSON')
    for field in ('primary_source', 'experiment_id', 'evidence_location', 'coder_inference', 'verification_state'):
        if not row[field]:
            parser.error(f'{field} is required')
    if int(row['equivalence_score']) >= 4 and any(not row[field] for field in ('manipulation', 'comparison', 'held_constants', 'observable')):
        parser.error('scores 4–5 require manipulation, comparison, held constants, and observable')
    year = papers[row['paper_id']]['year']
    if row['status'] in {'PRECEDED', 'PARTIALLY_PRECEDED'} and year.isdigit() and int(year) > int(CONFIG['cutoff_date'][:4]):
        parser.error('candidate year is after the study cutoff; verify the source date before coding')
    for field in ('reviewer_decision','reviewer_notes','reviewed_date','adjudicated_status','adjudicated_equivalence_score','adjudicator','adjudication_timestamp','review_batch_id'):
        if row[field]:
            parser.error('new proposals cannot contain review decisions')
    paper = papers[row['paper_id']]
    for field in ('title','authors','year','venue','url','doi','source_found','stage'):
        row[field] = paper[field]
    required = review_required(row)
    row.update(manual_review_required='TRUE' if required else 'FALSE',
               manual_review_status='PENDING' if required else 'NOT_REQUIRED',
               adjudication_authority='AGENT_PROVISIONAL', retrieved_date=date.today().isoformat())
    append_rows(path, fields, [row])
    print(f"Added {row['evidence_id']}; human review required: {required}")

if __name__ == '__main__':
    main()
