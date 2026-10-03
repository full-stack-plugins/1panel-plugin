"""Create a verified versioned archive without credentials, caches or local executables."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {'.git', '__pycache__', 'node_modules', '.venv', 'dist', '.test-data'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    if args.output.resolve() == ROOT:
        parser.error('Use a separate output directory, not the package root.')
    for checker in ['validate_portable_plugin.py', 'validate_markdown_links.py', 'check_snapshot.py']:
        subprocess.run([sys.executable, str(ROOT / 'scripts' / checker)], cwd=ROOT, check=True)
    manifest = json.loads((ROOT / 'plugin.json').read_text(encoding='utf-8'))
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output / f"{manifest['name']}-{manifest['version']}.zip"
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as package:
        for file in sorted(ROOT.rglob('*')):
            relative = file.relative_to(ROOT)
            if any(p in EXCLUDED for p in relative.parts) or not file.is_file() or file.is_symlink():
                continue
            if args.output.resolve() in file.resolve().parents:
                continue
            if file.name in {'connection.json', 'credentials.json'} or file.suffix in {'.pyc', '.exe', '.log'}:
                continue
            info = zipfile.ZipInfo(relative.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 << 16)
            package.writestr(info, file.read_bytes())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest + '  ' + output.name + '\n', encoding='utf-8')
    print(json.dumps({'archive': str(output), 'sha256': digest, 'bytes': output.stat().st_size}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
