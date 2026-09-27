"""Offline acceptance and negative-control tests; no real provider requests."""
import csv
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
