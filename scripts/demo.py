#!/usr/bin/env python3
"""Run a synthetic, offline workflow in a NEW workspace. No network calls."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    env = dict(os.environ, STUDYSCOUT_WORKSPACE=str(workspace))
    def run(script, *arguments):
        subprocess.run([sys.executable, str(PACKAGE / 'scripts' / (script + '.py')), *map(str, arguments)], env=env, check=True)
    example = PACKAGE / 'examples'
    run('init_study', '--config', example / 'study.json', '--workspace', workspace)
    shutil.copyfile(example / 'seeds.csv', workspace / 'data/searches/seed-queries.csv')
    run('freeze_study')
    run('register_seed_set')
    result = workspace / 'data/searches/results/synthetic.csv'
    shutil.copyfile(example / 'results.csv', result)
    run('log_retrieval', '--execution-id', 'R-S1-000001', '--query-id', 'Q-S1-000001', '--source-id', 'S-02',
        '--pages', '1', '--result-count', '2', '--terminal', 'SOURCE_EXHAUSTED', '--status', 'COMPLETE',
        '--normalized-paths', 'data/searches/results/synthetic.csv', '--notes', 'SYNTHETIC offline fixture; no provider was contacted')
    run('ingest_results', '--execution-id', 'R-S1-000001')
    run('add_evidence', example / 'evidence.json')
    run('build_review_batch', '--batch-id', 'BATCH-001')
    run('assign_review_batch', '--batch-id', 'BATCH-001', '--evidence-id', 'EV-000001')
    run('apply_review_decisions', example / 'decisions.json')
    run('validate_records')
    run('build_matrix', '--output', 'data/synthesis/matrix.md')
    run('check_stopping_rule')
    print(f'Offline demo complete: {workspace / "data/synthesis/matrix.md"}')

if __name__ == '__main__':
    main()
