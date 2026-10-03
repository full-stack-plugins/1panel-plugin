#!/usr/bin/env python3
"""Build a pinned official source checkout with an already installed Go compiler."""
import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

COMMIT = 'a12b2d4ddae90f6b210b73b89ba2bc4b572dcd0c'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='Existing official mcp-1panel git checkout containing v1.0.0')
    parser.add_argument('--output', required=True, type=Path, help='New external executable path')
    args = parser.parse_args()
    try:
        if not args.output.is_absolute() or args.output.exists():
            raise ValueError('Output must be a new absolute path; existing binaries are never overwritten.')
        origin = subprocess.check_output(['git', '-C', str(args.source), 'remote', 'get-url', 'origin'], text=True).strip()
        if origin not in {'https://github.com/1Panel-dev/mcp-1panel.git', 'https://github.com/1Panel-dev/mcp-1panel'}:
            raise ValueError('Use the official source remote.')
        sha = subprocess.check_output(['git', '-C', str(args.source), 'rev-parse', 'v1.0.0^{commit}'], text=True).strip()
        if sha != COMMIT:
            raise ValueError('Official release ref no longer matches the reviewed commit.')
        archive = subprocess.check_output(['git', '-C', str(args.source), 'archive', '--format=tar', COMMIT])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='1panel-build-') as directory:
            with tarfile.open(fileobj=io.BytesIO(archive)) as package:
                package.extractall(directory, filter='data')
            env = os.environ.copy()
            env['GOTOOLCHAIN'] = 'local'  # Never install/upgrade Go implicitly.
            subprocess.run(['go', 'build', '-trimpath', '-o', str(args.output), '.'], cwd=directory, env=env, check=True)
        with args.output.open('rb') as binary:
            digest = hashlib.file_digest(binary, 'sha256').hexdigest()
        receipt = {'repository': 'https://github.com/1Panel-dev/mcp-1panel', 'ref': 'v1.0.0',
                   'commit': COMMIT, 'binary': str(args.output), 'binary_sha256': digest,
                   'go_version': subprocess.check_output(['go', 'version'], text=True).strip()}
        args.output.with_suffix(args.output.suffix + '.build.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps(receipt, indent=2))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
