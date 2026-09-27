#!/usr/bin/env python3
"""Validate study configuration, CSV relationships, evidence, and frozen controls."""
import csv
import json
import re
from collections import Counter
from datetime import date
from rig_common import ROOT, DATA, CONTROL, CONFIG, CLAIM_IDS, STAGES, STATUSES, QUERY_ORIGINS, TERMINALS, read_csv, split_claim_ids
from schemas import SCHEMAS, ID_RULES
from init_study import validate_config


def validate():
    errors = []
    try:
        validate_config(CONFIG)
    except (ValueError, KeyError, TypeError) as exc:
        return [f'invalid study specification: {exc}']
    records = {}
    for name, fields in SCHEMAS.items():
        try:
            with (DATA / name).open(newline='') as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                if reader.fieldnames != fields or any(None in row or None in row.values() for row in rows):
                    errors.append(f'{name}: schema or row-width mismatch')
                records[name] = rows
        except (OSError, csv.Error) as exc:
            errors.append(f'{name}: {type(exc).__name__}')
    if errors:
        return errors
    for name, (field, pattern) in ID_RULES.items():
        values = [row[field] for row in records[name]]
        if any(not re.fullmatch(pattern, value) for value in values):
            errors.append(f'{name}: invalid {field}')
        if any(count > 1 for count in Counter(values).values()):
            errors.append(f'{name}: duplicate {field}')
    seeds = {r['seed_id']: r for r in records['searches/seed-queries.csv']}
    queries = {r['query_id']: r for r in records['searches/queries.csv']}
    papers = {r['paper_id']: r for r in records['corpus/candidates.csv']}
    edges = {r['edge_id']: r for r in records['searches/citation-chains.csv']}
    ledger = {r['execution_id']: r for r in records['searches/retrieval-ledger.csv']}
    for number, row in enumerate(seeds.values(), 1):
        if row['ordinal'] != str(number) or not row['query_text'].strip() or not row['track'].strip():
            errors.append(f"{row['seed_id']}: invalid ordinal or empty query/track")
        try:
            date.fromisoformat(row['freeze_date'])
        except ValueError:
            errors.append(f"{row['seed_id']}: invalid freeze date")
    for row in list(seeds.values()) + list(queries.values()):
        claims = split_claim_ids(row['claim_ids'])
        if not claims or not claims.issubset(CLAIM_IDS):
            errors.append('seed/query references unknown or empty claims')
    parents = records['searches/query-parents.csv']
    for row in parents:
        parent_set = {'QUERY': queries, 'PAPER': papers, 'EDGE': edges}.get(row['parent_type'], {})
        if row['query_id'] not in queries or row['parent_id'] not in parent_set or row['relation'] != 'DERIVED_FROM':
            errors.append('invalid query genealogy link')
        elif row['parent_type'] == 'QUERY':
            child, parent = queries[row['query_id']], queries[row['parent_id']]
            if child['stage'] == 'STAGE_1_COLD' and parent['stage'] != 'STAGE_1_COLD':
                errors.append('cold query descends from an injected query')
            if child['generation'].isdigit() and parent['generation'].isdigit() and int(child['generation']) <= int(parent['generation']):
                errors.append('query generation must increase along parent links')
    for row in queries.values():
        if row['stage'] not in STAGES or row['query_origin'] not in QUERY_ORIGINS:
            errors.append('invalid query stage/origin')
        stage = '1' if row['stage'] == 'STAGE_1_COLD' else '2'
        if not row['query_id'].startswith(f'Q-S{stage}-'):
            errors.append('query ID/stage mismatch')
        if row['query_origin'] == 'SEED':
            seed = seeds.get(row['seed_id'])
            if not seed or row['generation'] != '0' or any(row[k] != seed[k] for k in ('track','claim_ids','query_text')):
                errors.append('query differs from frozen seed')
        elif not row['generation'].isdigit() or int(row['generation']) < 1 or not any(p['query_id'] == row['query_id'] for p in parents):
            errors.append('derived query lacks valid generation/parents')
        if row['query_origin'] == 'INJECTED' and row['stage'] == 'STAGE_1_COLD':
            errors.append('injected query entered cold stage')
    try:
        sources = {r['source_id'] for r in read_csv(CONTROL / 'SOURCE_REGISTER.csv')}
    except (OSError, KeyError):
        sources = set()
        errors.append('invalid source register')
    for row in ledger.values():
        query = queries.get(row['query_id'])
        if not query or row['stage'] != query['stage'] or row['source_id'] not in sources:
            errors.append('retrieval references unknown query/source or wrong stage')
        if row['terminal_condition'] not in TERMINALS or row['status'] not in ('COMPLETE','FAILED','BLOCKED'):
            errors.append('invalid retrieval terminal/status')
        if row['terminal_condition'] in ('API_FAILURE','RATE_LIMITED') and row['status'] != 'FAILED':
            errors.append('retrieval failure reported as success')
        for field in ('pages_retrieved','result_count','requested_page_size','serious_candidate_count'):
            if not row[field].isdigit():
                errors.append(f'invalid retrieval count: {field}')
    for row in records['corpus/discoveries.csv']:
        execution = ledger.get(row['execution_id'])
        if row['paper_id'] not in papers or not execution or row['query_id'] != execution['query_id'] or row['stage'] != execution['stage']:
            errors.append('invalid discovery relationship')
    for row in records['coding/evidence-matrix.csv']:
        label = row['evidence_id']
        if row['paper_id'] not in papers or row['claim_id'] not in CLAIM_IDS or row['stage'] not in STAGES:
            errors.append(f'{label}: unknown paper/claim/stage')
        if row['status'] not in STATUSES or not row['equivalence_score'].isdigit() or int(row['equivalence_score']) > 5:
            errors.append(f'{label}: invalid status/score')
            continue
        try:
            criteria = json.loads(row['criteria_json'])
            if not isinstance(criteria, dict) or set(criteria) != set(CONFIG['criteria']):
                errors.append(f'{label}: criteria_json must cover configured criteria exactly')
        except ValueError:
            errors.append(f'{label}: malformed criteria_json')
        if not row['evidence_location'] or not row['coder_inference']:
            errors.append(f'{label}: evidence location and reasoning are required')
        required = int(row['equivalence_score']) >= 4 or row['status'] == 'PRECEDED'
        if row['manual_review_required'] != ('TRUE' if required else 'FALSE'):
            errors.append(f'{label}: inconsistent mandatory review flag')
        if required:
            state = row['manual_review_status']
            if state in ('PENDING','NEEDS_SOURCE'):
                if row['adjudication_authority'] != 'AGENT_PROVISIONAL':
                    errors.append(f'{label}: pending review must remain provisional')
            elif state in ('ACCEPTED','REVISED'):
                if (row['adjudication_authority'] != 'HUMAN_ADJUDICATED' or not row['adjudicator']
                    or not row['adjudication_timestamp'] or row['adjudicated_status'] not in STATUSES
                    or row['adjudicated_equivalence_score'] not in tuple(map(str, range(6)))):
                    errors.append(f'{label}: completed review lacks valid human decision')
            else:
                errors.append(f'{label}: mandatory review cannot be skipped')
    if (CONTROL / 'freeze.json').exists():
        from release_guard import sealed
        errors.extend(sealed()[1])
    elif ledger:
        errors.append('retrieval records exist without frozen controls')
    return errors


def main():
    errors = validate()
    for error in errors:
        print(f'ERROR: {error}')
    print('VALIDATION FAILED' if errors else 'VALIDATION PASSED')
    return 1 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
