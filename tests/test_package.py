import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('snapshot', ROOT / 'scripts/check_snapshot.py')
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)


class SnapshotTests(unittest.TestCase):
    def test_relocation_preserves_full_source_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'plugin with spaces'
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'dist'))
            self.assertEqual(snapshot.validate(target), [])

    def test_a_changed_skill_or_missing_resource_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'plugin'
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc', 'dist'))
            resource = next((target / 'skills').glob('*/SKILL.md'))
            resource.write_text('changed source', encoding='utf-8')
            self.assertTrue(any('snapshot drift' in error for error in snapshot.validate(target)))


if __name__ == '__main__':
    unittest.main()
