"""Offline acceptance and negative-control tests; no real provider requests."""
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import api_search
import build_matrix
from unittest.mock import patch
import io
import urllib.error

class Workflow(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name) / 'study'
        self.env = dict(os.environ, STUDYSCOUT_WORKSPACE=str(self.workspace))
        self.run_script('init_study', '--config', ROOT / 'examples/study.json', '--workspace', self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    def run_script(self, script, *args, ok=True):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts' / f'{script}.py'), *map(str,args)], env=self.env, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def prepare(self):
        shutil.copyfile(ROOT / 'examples/seeds.csv', self.workspace / 'data/searches/seed-queries.csv')
        self.run_script('freeze_study')
        self.run_script('register_seed_set')

    def ingest(self):
        self.prepare()
        shutil.copyfile(ROOT / 'examples/results.csv', self.workspace / 'data/searches/results/demo.csv')
        self.run_script('log_retrieval', '--execution-id', 'R-S1-000001', '--query-id', 'Q-S1-000001', '--source-id', 'S-02', '--pages', '1', '--result-count', '2', '--terminal', 'SOURCE_EXHAUSTED', '--status', 'COMPLETE', '--normalized-paths', 'data/searches/results/demo.csv')
        self.run_script('ingest_results', '--execution-id', 'R-S1-000001')

    def rows(self, relative):
        with (self.workspace / 'data' / relative).open(newline='') as handle:
            return list(csv.DictReader(handle))

    def replace_rows(self, relative, rows):
        path = self.workspace / 'data' / relative
        with path.open(newline='') as handle:
            fields = csv.DictReader(handle).fieldnames
        with path.open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)

    def test_empty_workspace_valid_but_network_blocked(self):
        self.run_script('validate_records')
        self.run_script('release_guard', ok=False)
        self.run_script('freeze_study', ok=False)

    def test_freeze_detects_changed_claims(self):
        self.prepare()
        path = self.workspace / 'study.json'
        config = json.loads(path.read_text())
        config['claims'][0]['text'] = 'Changed after freezing'
        path.write_text(json.dumps(config))
        self.run_script('release_guard', ok=False)
        self.run_script('validate_records', ok=False)

    def test_frozen_manifest_cannot_be_overwritten(self):
        self.prepare()
        self.run_script('freeze_study', ok=False)

    def test_seed_registration_is_idempotent(self):
        self.prepare()
        self.run_script('register_seed_set')
        self.assertEqual(len(self.rows('searches/queries.csv')), 1)

    def test_modified_seeds_cannot_be_registered(self):
        self.prepare()
        with (self.workspace / 'data/searches/seed-queries.csv').open('a') as handle:
            handle.write('\n')
        self.run_script('register_seed_set', ok=False)

    def test_duplicate_paper_keeps_discovery_routes_and_reingest_is_idempotent(self):
        self.ingest()
        self.run_script('ingest_results', '--execution-id', 'R-S1-000001')
        self.assertEqual(len(self.rows('corpus/candidates.csv')), 1)
        self.assertEqual(len(self.rows('corpus/discoveries.csv')), 2)
        self.run_script('validate_records')

    def test_strong_evidence_requires_human_review(self):
        self.ingest()
        self.run_script('add_evidence', ROOT / 'examples/evidence.json')
        row = self.rows('coding/evidence-matrix.csv')[0]
        self.assertEqual(row['manual_review_status'], 'PENDING')
        self.assertEqual(row['adjudication_authority'], 'AGENT_PROVISIONAL')
        self.run_script('build_review_batch', '--batch-id', 'BATCH-001')
        self.run_script('assign_review_batch', '--batch-id', 'BATCH-001', '--evidence-id', 'EV-000001')
        self.run_script('apply_review_decisions', ROOT / 'examples/decisions.json')
        self.run_script('validate_records')
        result = self.run_script('build_matrix', '--stdout')
        self.assertIn('[HUMAN]', result.stdout)
        self.assertEqual(len(list((self.workspace / 'data/reviews/history').glob('*-before.csv'))), 1)

    def test_unknown_criterion_rejected_without_append(self):
        self.ingest()
        record = json.loads((ROOT / 'examples/evidence.json').read_text())
        record['criteria_json'] = '{"unconfigured": "YES"}'
        path = Path(self.temp.name) / 'bad.json'
        path.write_text(json.dumps(record))
        self.run_script('add_evidence', path, ok=False)
        self.assertFalse(self.rows('coding/evidence-matrix.csv'))

    def test_partial_precedence_requires_review_and_duplicate_locus_is_rejected(self):
        self.ingest()
        record = json.loads((ROOT / 'examples/evidence.json').read_text())
        record['equivalence_score'] = '3'
        path = Path(self.temp.name) / 'partial.json'
        path.write_text(json.dumps(record))
        self.run_script('add_evidence', path)
        self.assertEqual(self.rows('coding/evidence-matrix.csv')[0]['manual_review_required'], 'TRUE')
        record['evidence_id'] = 'EV-000002'
        path.write_text(json.dumps(record))
        self.run_script('add_evidence', path, ok=False)
        self.assertEqual(len(self.rows('coding/evidence-matrix.csv')), 1)

    def test_validator_rejects_missing_source_and_inconsistent_screening(self):
        self.ingest()
        self.run_script('add_evidence', ROOT / 'examples/evidence.json')
        evidence = self.rows('coding/evidence-matrix.csv')
        evidence[0]['primary_source'] = ''
        self.replace_rows('coding/evidence-matrix.csv', evidence)
        self.run_script('validate_records', ok=False)
        evidence[0]['primary_source'] = 'Synthetic source'
        self.replace_rows('coding/evidence-matrix.csv', evidence)
        candidate = self.rows('corpus/candidates.csv')[0]
        self.replace_rows('corpus/screening.csv', [{'paper_id': candidate['paper_id'], 'title': candidate['title'],
            'decision': 'EXCLUDED', 'basis': 'unrelated', 'date_utc': '2026-01-01'}])
        self.run_script('validate_records', ok=False)

    def test_post_cutoff_candidate_cannot_be_coded_as_precedent(self):
        self.ingest()
        candidates = self.rows('corpus/candidates.csv')
        candidates[0]['year'] = '2026'
        self.replace_rows('corpus/candidates.csv', candidates)
        record = json.loads((ROOT / 'examples/evidence.json').read_text())
        record.update(status='PRECEDED', equivalence_score='5')
        path = Path(self.temp.name) / 'post-cutoff.json'
        path.write_text(json.dumps(record))
        self.run_script('add_evidence', path, ok=False)

    def test_final_seal_detects_changed_and_added_files(self):
        self.ingest()
        self.run_script('seal_study')
        self.run_script('seal_study', '--verify')
        candidate_path = self.workspace / 'data/corpus/candidates.csv'
        original = candidate_path.read_bytes()
        candidate_path.write_bytes(original + b'\n')
        self.run_script('seal_study', '--verify', ok=False)
        candidate_path.write_bytes(original)
        (self.workspace / 'extra.txt').write_text('new')
        self.run_script('seal_study', '--verify', ok=False)

    def test_reported_total_cannot_be_logged_as_source_exhausted(self):
        self.prepare()
        self.run_script('log_retrieval', '--execution-id', 'R-S1-000001', '--query-id', 'Q-S1-000001',
            '--source-id', 'S-02', '--pages', '1', '--result-count', '1', '--results-available', '50',
            '--terminal', 'SOURCE_EXHAUSTED', '--status', 'COMPLETE')
        self.run_script('validate_records', ok=False)

    def test_stopping_uses_adjudicated_score_and_round_retrieval(self):
        self.ingest()
        self.run_script('add_evidence', ROOT / 'examples/evidence.json')
        evidence = self.rows('coding/evidence-matrix.csv')
        evidence[0].update(adjudication_authority='HUMAN_ADJUDICATED', adjudicated_equivalence_score='1',
                           adjudicated_status='ADJACENT', manual_review_status='REVISED')
        self.replace_rows('coding/evidence-matrix.csv', evidence)
        candidates = self.rows('corpus/candidates.csv')
        candidates[0]['first_seen_round_id'] = 'ROUND-S1-001'
        self.replace_rows('corpus/candidates.csv', candidates)
        rounds = []
        coverage = []
        triggers = []
        for ordinal in (1, 2):
            round_id = f'ROUND-S1-{ordinal:03d}'
            rounds.append(dict(round_id=round_id, stage='STAGE_1_COLD', ordinal=str(ordinal),
                completed_at='2026-01-01', trigger_paper_count='1', new_candidates_count='1' if ordinal == 1 else '0',
                new_provisional_ge4_count='0', new_productive_family_count='0', complete='TRUE', machine_null='TRUE'))
            coverage.append(dict(coverage_id=f'COV-S1-{ordinal:06d}', round_id=round_id,
                paper_id='P-000001', backward_status='COMPLETE', forward_status='COMPLETE',
                author_status='COMPLETE', terminology_status='COMPLETE'))
            triggers.append(dict(round_id=round_id, paper_id='P-000001'))
        self.replace_rows('searches/expansion-rounds.csv', rounds)
        self.replace_rows('searches/expansion-coverage.csv', coverage)
        self.replace_rows('searches/round-triggers.csv', triggers)
        for ordinal in (1, 2):
            query_id = f'Q-S1-{ordinal + 1:06d}'
            self.run_script('register_query', '--query-id', query_id, '--origin', 'TERMINOLOGY',
                '--query', f'synthetic followup {ordinal}', '--track', 'terminology', '--claims', 'C1',
                '--generation', '1', '--parent-query-id', 'Q-S1-000001',
                '--expansion-round-id', f'ROUND-S1-{ordinal:03d}')
            self.run_script('log_retrieval', '--execution-id', f'R-S1-{ordinal + 1:06d}',
                '--query-id', query_id, '--source-id', 'S-02', '--pages', '1', '--result-count', '0',
                '--results-available', '0', '--terminal', 'SOURCE_EXHAUSTED', '--status', 'COMPLETE')
        self.assertIn('STOPPING CONDITION SATISFIED;', self.run_script('check_stopping_rule').stdout)
        ledger = self.rows('searches/retrieval-ledger.csv')
        ledger[-1]['terminal_condition'] = 'PAGE_LIMIT_REACHED'
        self.replace_rows('searches/retrieval-ledger.csv', ledger)
        self.run_script('check_stopping_rule', '--write-status', 'synthesis/invalid.md', ok=False)
        self.assertFalse((self.workspace / 'data/synthesis/invalid.md').exists())

    def test_no_rounds_does_not_satisfy_stopping(self):
        result = self.run_script('check_stopping_rule')
        self.assertIn('NOT SATISFIED', result.stdout)

    def test_dangling_genealogy_detected(self):
        self.prepare()
        self.run_script('register_query', '--query-id', 'Q-S1-000002', '--origin', 'DISCOVERED', '--query', 'cache scheduling', '--track', 'terms', '--claims', 'C1', '--generation', '1', '--parent-query-id', 'Q-S1-999999')
        self.run_script('validate_records', ok=False)

class MatrixRanking(unittest.TestCase):
    def test_human_lowering_changes_display_ranking(self):
        lowered = dict(adjudication_authority='HUMAN_ADJUDICATED', adjudicated_equivalence_score='1',
                       adjudicated_status='ADJACENT', equivalence_score='5', status='PRECEDED', evidence_id='EV-000001')
        pending = dict(adjudication_authority='AGENT_PROVISIONAL', equivalence_score='3', status='ADJACENT', evidence_id='EV-000002')
        self.assertGreater(build_matrix.rank(pending), build_matrix.rank(lowered))


class Retrieval(unittest.TestCase):
    setUp = Workflow.setUp
    tearDown = Workflow.tearDown
    run_script = Workflow.run_script
    prepare = Workflow.prepare
    rows = Workflow.rows
    def mocked_request(self, response=None, error=None, max_pages=1):
        self.prepare()
        workspace = self.workspace
        with patch.multiple(api_search, QUERIES=workspace/'data/searches/queries.csv',
                            LEDGER=workspace/'data/searches/retrieval-ledger.csv',
                            RAW=workspace/'data/searches/raw', RESULTS=workspace/'data/searches/results',
                            CONTROL=workspace/'control', DATA=workspace/'data'), \
             patch.object(api_search, 'require_release'), \
             patch('validate_records.validate', return_value=[]), \
             patch.object(sys, 'argv', ['api_search.py', '--source','crossref','--query-id','Q-S1-000001',
                                       '--execution-id','R-S1-000001','--page-size','1','--max-pages',str(max_pages)]), \
             patch.object(api_search.urllib.request, 'urlopen', side_effect=error, return_value=io.BytesIO(response or b'')), \
             patch.object(api_search.time, 'sleep'):
            return api_search.main()

    def test_page_budget_not_source_exhaustion(self):
        payload = b'{"message":{"items":[{"title":["Synthetic"]}],"total-results":50,"next-cursor":"next"}}'
        self.assertEqual(self.mocked_request(payload), 0)
        row = self.rows('searches/retrieval-ledger.csv')[0]
        self.assertEqual(row['terminal_condition'], 'PAGE_LIMIT_REACHED')
        self.assertEqual(row['result_count'], '1')
        receipt = json.loads(row['parameters_json'])['requests'][0]
        self.assertEqual(receipt['sha256'], hashlib.sha256(payload).hexdigest())
        self.assertIn('query.bibliographic=', receipt['url_with_contact_redacted'])

    def test_provider_total_prevents_false_exhaustion(self):
        payload = b'{"message":{"items":[],"total-results":50}}'
        self.assertEqual(self.mocked_request(payload), 0)
        row = self.rows('searches/retrieval-ledger.csv')[0]
        self.assertEqual(row['terminal_condition'], 'API_TRUNCATED')
        self.assertEqual(row['api_truncated'], 'TRUE')

    def test_request_receipt_redacts_contact_email(self):
        url = api_search.openalex_url('synthetic query', 10, '*', 'private@example.org')
        safe = api_search.safe_request_url(url)
        self.assertNotIn('private@example.org', safe)
        self.assertIn('REDACTED', safe)

    def test_unapplied_api_filters_are_rejected(self):
        with patch.object(sys, 'argv', ['api_search.py', '--source', 'crossref', '--query-id', 'Q-S1-000001',
                                         '--execution-id', 'R-S1-000001', '--filters', 'year:2020']):
            with self.assertRaises(SystemExit) as caught:
                api_search.main()
        self.assertEqual(caught.exception.code, 2)

    def test_rate_limit_remains_failed_execution(self):
        error = urllib.error.HTTPError('https://example.org',429,'Too Many Requests',{},None)
        self.assertEqual(self.mocked_request(error=error), 1)
        row = self.rows('searches/retrieval-ledger.csv')[0]
        self.assertEqual(row['terminal_condition'], 'RATE_LIMITED')
        self.assertEqual(row['status'], 'FAILED')

    def test_html_challenge_remains_blocked(self):
        self.assertEqual(self.mocked_request(b'<html>challenge</html>'), 1)
        self.assertEqual(self.rows('searches/retrieval-ledger.csv')[0]['terminal_condition'], 'ACCESS_BLOCKED')

    def test_malformed_payload_is_logged_as_failure(self):
        self.assertEqual(self.mocked_request(b'not json'), 1)
        self.assertEqual(self.rows('searches/retrieval-ledger.csv')[0]['terminal_condition'], 'API_FAILURE')


class Parsers(unittest.TestCase):
    def test_openalex_cursor_is_retained(self):
        page = api_search.parse_openalex(json.dumps({'results': [{'title':'Synthetic','publication_year':2025}], 'meta': {'count':2,'next_cursor':'next'}}).encode(), 'synthetic.json', 1, 0)
        self.assertFalse(page.exhausted)
        self.assertEqual(page.next_token, 'next')
        self.assertEqual(page.rows[0]['source_position'], '1')

    def test_crossref_empty_page_is_exhausted(self):
        page = api_search.parse_crossref(b'{"message":{"items":[],"total-results":0}}', 'synthetic.json', 50, 0)
        self.assertTrue(page.exhausted)

    def test_semantic_cap_is_not_exhaustion(self):
        page = api_search.parse_semantic(b'{"data":[{"title":"Synthetic"}],"next":1000,"total":2000}', 'synthetic.json', 1, 999)
        self.assertTrue(page.capped)
        self.assertFalse(page.exhausted)
        self.assertEqual(page.rows[0]['peer_reviewed_hint'], 'UNKNOWN')

    def test_dblp_single_hit(self):
        data = {'result':{'hits':{'@total':'1','hit':{'info':{'title':'Synthetic','authors':{'author':'Example'}}}}}}
        page = api_search.parse_dblp(json.dumps(data).encode(), 'synthetic.json', 50, 0)
        self.assertEqual(page.rows[0]['authors'], 'Example')
        self.assertTrue(page.exhausted)

    def test_arxiv_empty_feed(self):
        page = api_search.parse_arxiv(b'<feed xmlns="http://www.w3.org/2005/Atom"/>', 'synthetic.xml', 50, 0)
        self.assertTrue(page.exhausted)

if __name__ == '__main__':
    unittest.main()
