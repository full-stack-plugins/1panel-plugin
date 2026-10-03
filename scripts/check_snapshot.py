"""Verify declared source-snapshot bytes; no download, source rewrite or implicit update."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(root):
    errors = []
    root = root.resolve()
    spec = importlib.util.spec_from_file_location('skill_vendor', root / 'scripts/vendor/skill_vendor.py')
    vendor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vendor)
    try:
        lock = vendor.load_lock(root / 'skills.lock.json')
        vendor.validate_no_cross_source_collisions(lock)
        vendor.validate_plugin_local_inventory(root, lock)
        policy = json.loads((root / 'plugin-local-skills.json').read_text(encoding='utf-8'))
        if policy['skills']:
            errors.append('Local skill exceptions are not allowed; maintain skills in source packages')
        for source in lock['sources']:
            destination = vendor.validate_source(source, root)
            if not vendor.COMMIT_SHA_RE.fullmatch(source.get('sha', '')):
                errors.append('Missing immutable source commit')
            for name in source['skills']:
                skill = destination / name
                if any(p.is_symlink() for p in skill.rglob('*')):
                    errors.append(f'{name}: unexpected symlink')
                if not (skill / 'SKILL.md').is_file() or vendor.hash_skill_dir(skill) != source.get('sha256', {}).get(name):
                    errors.append(f'{name}: source snapshot drift')
    except (ValueError, RuntimeError, KeyError) as error:
        errors.append(str(error))
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
