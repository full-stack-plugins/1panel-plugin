"""Verify declared source-snapshot bytes; no download, source rewrite or implicit update."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(root):
    errors = []
    root = root.resolve()
    lock = json.loads((root / 'skills.lock.json').read_text(encoding='utf-8'))
    local = json.loads((root / 'plugin-local-skills.json').read_text(encoding='utf-8'))['skills']
    actual = {p.name for p in (root / 'skills').iterdir() if p.is_dir()}
    declared = set(lock['skills']) | set(local)
    if actual != declared or set(lock['skills']) & set(local):
        errors.append('Source/local inventory differs from discovered skills')
    for name, expected in lock['skills'].items():
        base = root / 'skills' / name
        observed = {}
        for file in base.rglob('*'):
            if '__pycache__' in file.parts or file.suffix == '.pyc':
                continue
            if file.is_symlink():
                errors.append(f'{name}: unexpected symlink')
            elif file.is_file():
                observed[file.relative_to(base).as_posix()] = hashlib.sha256(file.read_bytes()).hexdigest()
        for relative in sorted(set(observed) | set(expected)):
            if observed.get(relative) != expected.get(relative):
                errors.append(f'{name}/{relative}: snapshot drift')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    errors = validate(args.root)
    print(json.dumps({'valid': not errors, 'errors': errors}, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
