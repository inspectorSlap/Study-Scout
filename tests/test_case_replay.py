"""Offline guarantees of the public real-case replay."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'case-studies/eytzinger-search'
spec = importlib.util.spec_from_file_location('replay_case', ROOT / 'scripts/replay_case.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)

class CaseReplayTests(unittest.TestCase):
    def test_real_snapshot_reproduces_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / 'replay'
            command = [sys.executable, str(ROOT / 'scripts/replay_case.py'), '--case', str(CASE), '--workspace', str(dest)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertIn('byte-for-byte', first.stdout)
            self.assertIn('NOT SATISFIED', (dest / 'data/synthesis/stopping.md').read_text())
            before = (dest / 'data/coding/evidence-matrix.csv').read_bytes()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn('refusing to overwrite', second.stderr)
            self.assertEqual(before, (dest / 'data/coding/evidence-matrix.csv').read_bytes())

    def test_changed_or_unmanifested_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory) / 'case'
            shutil.copytree(CASE, case)
            target = case / 'snapshot/study.json'
            original = target.read_bytes()
            target.write_bytes(original + b'\n')
            with self.assertRaisesRegex(ValueError, 'artifact changed'):
                replay.verify(case)
            target.write_bytes(original)
            (case / 'snapshot/unexpected.txt').write_text('unexpected')
            with self.assertRaisesRegex(ValueError, 'unmanifested'):
                replay.verify(case)

    def test_manifest_cannot_escape_case(self):
        with tempfile.TemporaryDirectory() as directory:
            case = Path(directory) / 'case'
            shutil.copytree(CASE, case)
            outside = Path(directory) / 'outside'
            outside.write_text('outside')
            manifest = json.loads((case / 'MANIFEST.json').read_text())
            manifest['sha256']['../outside'] = hashlib.sha256(outside.read_bytes()).hexdigest()
            (case / 'MANIFEST.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'unsafe manifest path'):
                replay.verify(case)

if __name__ == '__main__':
    unittest.main()
