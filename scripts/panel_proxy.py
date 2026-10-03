#!/usr/bin/env python3
"""Policy boundary around the pinned official mcp-1panel stdio process.

No SDK, HTTP implementation, installer or secret-bearing command arguments.
The official server remains responsible for MCP schemas and panel API calls.
"""
import argparse
import hashlib
import ipaddress
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

ACCESS = {'readonly': 0, 'readwrite': 1, 'full': 2}
TOOLS = {
    'get_dashboard_info': 0, 'get_system_info': 0,
    'list_websites': 0, 'list_ssls': 0,
    'list_installed_apps': 0, 'list_databases': 0,
    'create_website': 1, 'create_ssl': 1, 'create_database': 1,
    'install_openresty': 2, 'install_mysql': 2,
}
MAX_LINE = 1024 * 1024
MAX_PENDING = 32
REQUEST_TIMEOUT = 60


class ConfigError(ValueError):
    pass


def allowed(name, level):
    return name in TOOLS and level in ACCESS and TOOLS[name] <= ACCESS[level]


def validate_host(host):
    try:
        url = urlsplit(host)
        _ = url.port
        if (url.scheme not in {'http', 'https'} or not url.hostname or url.username
                or url.password or url.query or url.fragment or url.path not in {'', '/'}):
            raise ValueError()
        loopback = url.hostname == 'localhost'
        try:
            loopback = loopback or ipaddress.ip_address(url.hostname).is_loopback
        except ValueError:
            pass
        if url.scheme == 'http' and not loopback:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ConfigError('Panel host must be an HTTPS origin (HTTP is allowed only on loopback).') from None


def validate_binary(binary, digest):
    if not isinstance(binary, str) or not Path(binary).is_absolute():
        raise ConfigError('Official binary must have an absolute path.')
    if not isinstance(digest, str) or not re.fullmatch('[a-f0-9]{64}', digest):
        raise ConfigError('Configure the verified official binary SHA256.')
    try:
        with Path(binary).open('rb') as handle:
            actual = hashlib.file_digest(handle, 'sha256').hexdigest()
    except OSError:
        raise ConfigError('Configured official binary is not readable.') from None
    if actual != digest:
        raise ConfigError('Official binary SHA256 mismatch; re-verify the installation.')


def private_json(path):
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 65536:
            raise ValueError()
        if os.name != 'nt' and path.stat().st_mode & 0o077:
            raise ValueError()
        value = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except (OSError, ValueError):
        raise ConfigError('Private connection/credentials configuration is missing, invalid or insufficiently protected.') from None


def load_config(data):
    config = private_json(data / 'connection.json')
    if set(config) != {'binary', 'binary_sha256', 'host', 'access_level', 'upstream_commit'}:
        raise ConfigError('Connection configuration fields are invalid.')
    if not isinstance(config['access_level'], str) or config['access_level'] not in ACCESS:
        raise ConfigError('Access level must be readonly, readwrite or full.')
    if config['upstream_commit'] != 'a12b2d4ddae90f6b210b73b89ba2bc4b572dcd0c':
        raise ConfigError('This plugin supports the pinned official v1.0.0 source; review other versions first.')
    validate_host(config['host'])
    validate_binary(config['binary'], config['binary_sha256'])
    credentials = private_json(data / 'credentials.json')
    token = credentials.get('panel_access_token')
    if set(credentials) != {'panel_access_token'} or not isinstance(token, str) or not token.strip() or '\n' in token or '\r' in token:
        raise ConfigError('Configure a nonempty private panel access token.')
    return config, token


def rpc_error(identity, code, message):
    return {'jsonrpc': '2.0', 'id': identity, 'error': {'code': code, 'message': message}}


def tool_error(identity, message):
    return {'jsonrpc': '2.0', 'id': identity, 'result': {
        'isError': True, 'content': [{'type': 'text', 'text': message}]}}


def read_lines(stream, events, origin):
    try:
        while True:
            line = stream.readline(MAX_LINE + 1)
            if not line:
                events.put((origin, None))
                return
            if len(line) > MAX_LINE:
                events.put((origin, 'oversized'))
                return
            try:
                message = json.loads(line)
            except (ValueError, UnicodeError):
                message = 'malformed'
            events.put((origin, message))
    except (OSError, ValueError):
        events.put((origin, None))


def serve(config, token, data, input_stream=None, output_stream=None, timeout=REQUEST_TIMEOUT):
    source = input_stream or sys.stdin.buffer
    output = output_stream or sys.stdout
    runtime = data / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    environment = os.environ.copy()
    environment.update(PANEL_HOST=config['host'], PANEL_ACCESS_TOKEN=token)
    environment.pop('MCP_AUTH_TOKEN', None)
    child = subprocess.Popen([config['binary'], '-transport', 'stdio'],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, cwd=runtime, env=environment)
    events = queue.Queue(maxsize=128)
    for stream, origin in [(source, 'client'), (child.stdout, 'server')]:
        threading.Thread(target=read_lines, args=(stream, events, origin), daemon=True).start()
    pending = {}
    serial = 0
    client_closed = False
    initialize_complete = False

    def emit(message):
        # Upstream errors or reflection must never expose the configured API key.
        def redact(value):
            if isinstance(value, str):
                return value.replace(token, '[REDACTED]')
            if isinstance(value, list):
                return [redact(item) for item in value]
            if isinstance(value, dict):
                return {redact(key): redact(item) for key, item in value.items()}
            return value
        wire = json.dumps(redact(message), ensure_ascii=False, separators=(',', ':'))
        output.write(wire + '\n')
        output.flush()

    def send(message):
        child.stdin.write((json.dumps(message, separators=(',', ':')) + '\n').encode())
        child.stdin.flush()

    try:
        while True:
            if client_closed and not pending:
                return 0
            try:
                origin, message = events.get(timeout=0.1)
            except queue.Empty:
                origin, message = None, None
            if origin == 'server' and (message is None or not isinstance(message, dict)):
                for record in pending.values():
                    emit(tool_error(record['id'], 'Official MCP server exited or violated framing; outcome is unknown. Reconcile before retry.')
                         if record['method'] == 'tools/call' else rpc_error(record['id'], -32603, 'Official MCP server unavailable.'))
                return 1
            if origin == 'client':
                if message is None:
                    client_closed = True
                    continue
                if message == 'oversized':
                    emit(rpc_error(None, -32600, 'Request exceeds the framing limit.'))
                    client_closed = True
                    continue
                if message == 'malformed':
                    emit(rpc_error(None, -32700, 'Invalid JSON.'))
                    continue
                if not isinstance(message, dict) or message.get('jsonrpc') != '2.0' or not isinstance(message.get('method'), str):
                    emit(rpc_error(None, -32600, 'Invalid JSON-RPC request.'))
                    continue
                method = message['method']
                identity = message.get('id')
                if 'id' not in message:
                    if method == 'notifications/initialized' and initialize_complete:
                        send(message)
                    elif method == 'notifications/cancelled':
                        params = message.get('params', {})
                        if isinstance(params, dict):
                            for wire_id, record in pending.items():
                                if record['id'] == params.get('requestId'):
                                    send({**message, 'params': {**params, 'requestId': wire_id}})
                    continue
                if isinstance(identity, bool) or not isinstance(identity, (str, int)):
                    emit(rpc_error(None, -32600, 'Request ID must be a string or integer.'))
                    continue
                if method not in {'initialize', 'ping', 'tools/list', 'tools/call'}:
                    emit(rpc_error(identity, -32601, 'Method is not supported by this tool-only plugin.'))
                    continue
                if method != 'initialize' and not initialize_complete:
                    emit(rpc_error(identity, -32000, 'Initialize the MCP session first.'))
                    continue
                if method == 'initialize' and (initialize_complete or any(r['method'] == 'initialize' for r in pending.values())):
                    emit(rpc_error(identity, -32600, 'Session already initialized or initializing.'))
                    continue
                params = message.get('params', {})
                if not isinstance(params, dict):
                    emit(rpc_error(identity, -32602, 'Parameters must be an object.'))
                    continue
                if method == 'tools/call':
                    if not isinstance(params.get('name'), str) or not isinstance(params.get('arguments', {}), dict):
                        emit(rpc_error(identity, -32602, 'Tool name and arguments are invalid.'))
                        continue
                    if not allowed(params['name'], config['access_level']):
                        emit(tool_error(identity, 'Tool is not allowed by the configured access level or pinned capability policy.'))
                        continue
                if len(pending) >= MAX_PENDING or any(r['id'] == identity for r in pending.values()):
                    emit(rpc_error(identity, -32000, 'Request limit reached or duplicate in-flight ID.'))
                    continue
                serial += 1
                pending[serial] = {'id': identity, 'method': method, 'deadline': time.monotonic() + timeout}
                send({**message, 'id': serial})
            elif origin == 'server' and isinstance(message, dict):
                if message.get('jsonrpc') != '2.0':
                    return 1
                if 'method' in message:
                    if 'id' in message:
                        send(rpc_error(message['id'], -32601, 'Server-initiated requests are unsupported.'))
                    continue
                if 'id' not in message:
                    # No upstream request can elicit sampling, elicitation or roots access.
                    continue
                if isinstance(message['id'], bool) or not isinstance(message['id'], (str, int)):
                    return 1
                record = pending.pop(message['id'], None)
                if record is None:
                    continue  # late response to a timed-out request
                result = message.get('result')
                if record['method'] == 'initialize' and isinstance(result, dict):
                    initialize_complete = True
                    result['capabilities'] = {'tools': {}}
                if record['method'] == 'tools/list' and isinstance(result, dict):
                    if not isinstance(result.get('tools'), list):
                        emit(rpc_error(record['id'], -32603, 'Official tool discovery returned invalid data.'))
                        continue
                    result['tools'] = [tool for tool in result.get('tools', [])
                                       if isinstance(tool, dict) and allowed(tool.get('name'), config['access_level'])]
                emit({**message, 'id': record['id']})
            now = time.monotonic()
            for wire_id, record in list(pending.items()):
                if record['deadline'] <= now:
                    del pending[wire_id]
                    emit(tool_error(record['id'], 'Request timed out; outcome is unknown. Inspect panel state before retrying. No retry was submitted.')
                         if record['method'] == 'tools/call' else rpc_error(record['id'], -32000, 'Official MCP request timed out.'))
    except (BrokenPipeError, OSError):
        return 1
    finally:
        if child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=5)
        for stream in (child.stdin, child.stdout):
            stream.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True, type=Path)
    arguments = parser.parse_args()
    try:
        if not arguments.data.is_absolute():
            raise ConfigError('Supply an absolute plugin data directory.')
        config, token = load_config(arguments.data)
        return serve(config, token, arguments.data)
    except ConfigError as error:
        print(f'1Panel setup required: {error}', file=sys.stderr)
        return 2
    except OSError:
        print('1Panel official MCP process could not start; check the configured executable.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
