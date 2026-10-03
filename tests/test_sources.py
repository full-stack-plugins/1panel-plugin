import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('snapshot_source_tests', ROOT / 'scripts/check_snapshot.py')
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


class SourceOwnershipTests(unittest.TestCase):
    def test_all_skills_have_immutable_source_ownership(self):
        lock = json.loads((ROOT / 'skills.lock.json').read_text(encoding='utf-8'))
        self.assertTrue(lock.get('sources'), 'An immutable source release is required')
        for source in lock['sources']:
            self.assertRegex(source['ref'], r'^v\d+\.\d+\.\d+$')
            self.assertRegex(source['sha'], r'^[a-f0-9]{40}$')
        self.assertEqual(json.loads((ROOT / 'plugin-local-skills.json').read_text())['skills'], [])

    def test_untracked_resource_addition_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'relocated plugin'
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'dist'))
            first = next((target / 'skills').iterdir())
            (first / 'unreviewed-resource.txt').write_text('extra resource', encoding='utf-8')
            self.assertTrue(snapshot.validate(target))


if __name__ == '__main__':
    unittest.main()
