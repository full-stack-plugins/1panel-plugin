#!/usr/bin/env python3
"""Explicit private setup; never called on plugin load. No provider installation."""
import argparse
import csv
import getpass
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from panel_proxy import ACCESS, ConfigError, validate_binary, validate_host

COMMIT = 'a12b2d4ddae90f6b210b73b89ba2bc4b572dcd0c'


def protect(path):
    if os.name == 'nt':
        identity = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'],
                                  capture_output=True, text=True, check=True)
        sid = list(csv.reader(identity.stdout.strip().splitlines()))[0][1]
        subprocess.run(['icacls', str(path), '/inheritance:r', '/grant:r', f'*{sid}:(F)'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    else:
        path.chmod(0o700 if path.is_dir() else 0o600)


def write_private(path, value):
    descriptor, name = tempfile.mkstemp(prefix='.setup-', dir=path.parent)
    temporary = Path(name)
    try:
        os.close(descriptor)
        protect(temporary)
        temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--binary', required=True)
    parser.add_argument('--binary-sha256', required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--access-level', choices=list(ACCESS), default='readonly')
    parser.add_argument('--replace', action='store_true', help='Explicitly replace existing private settings')
    parser.add_argument('--token-stdin', action='store_true', help='Read key from private redirected stdin; never command arguments')
    args = parser.parse_args()
    try:
        if not args.data.is_absolute():
            raise ConfigError('Data directory must be absolute and supplied by the client.')
        validate_host(args.host)
        validate_binary(args.binary, args.binary_sha256)
        if not args.replace and any((args.data / name).exists() for name in ['connection.json', 'credentials.json']):
            raise ConfigError('Configuration already exists; inspect it or explicitly use --replace.')
        args.data.mkdir(parents=True, exist_ok=True, mode=0o700)
        protect(args.data)
        token = sys.stdin.readline().rstrip('\r\n') if args.token_stdin else getpass.getpass('1Panel API key (hidden): ')
        if not token.strip() or '\n' in token or '\r' in token:
            raise ConfigError('API key is empty or invalid.')
        write_private(args.data / 'credentials.json', {'panel_access_token': token})
        write_private(args.data / 'connection.json', {
            'binary': str(Path(args.binary).resolve()), 'binary_sha256': args.binary_sha256,
            'host': args.host.rstrip('/'), 'access_level': args.access_level, 'upstream_commit': COMMIT})
        print(f'Private configuration saved. Access level: {args.access_level}. Restart the MCP connection.')
        return 0
    except (ConfigError, OSError, subprocess.SubprocessError) as error:
        message = str(error) if isinstance(error, ConfigError) else 'Private configuration could not be secured or saved.'
        print(message, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
