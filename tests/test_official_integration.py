"""Real official executable through the shipped proxy; simulated loopback panel API."""
import hashlib
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINARY = os.environ.get('ONEPANEL_TEST_BINARY')
TOKEN = 'TEST-key-"quote-and-backslash\\'
READS = {'get_system_info', 'get_dashboard_info', 'list_websites', 'list_ssls', 'list_databases', 'list_installed_apps'}
CREATES = {'create_website', 'create_ssl', 'create_database'}
INSTALLS = {'install_mysql', 'install_openresty'}


class PanelHandler(BaseHTTPRequestHandler):
    def log_message(self, *arguments):
        pass

    def do_GET(self):
        self.respond()

    def do_POST(self):
        self.respond()

    def respond(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))) or '{}')
        timestamp = self.headers.get('1Panel-Timestamp', '')
        digest = hashlib.md5(('1panel' + TOKEN + timestamp).encode()).hexdigest()
        self.server.requests.append({'path': self.path, 'body': body,
                                     'auth': bool(timestamp) and self.headers.get('1Panel-Token') == digest,
                                     'leaked': TOKEN in str(dict(self.headers))})
        if self.server.delay:
            time.sleep(self.server.delay)
        data = {'code': 200, 'message': TOKEN if self.server.reflect else 'success', 'data': {}}
        if self.path.endswith('/dashboard/base/os'):
            data['data'] = {'os': 'test-linux', 'kernelArch': 'amd64'}
        elif self.path.endswith('/dashboard/base/all/all'):
            data['data'] = {'hostname': 'loopback-test-panel', 'websiteNumber': 1}
        elif self.path.endswith('/groups/search'):
            data['data'] = [{'id': 1, 'isDefault': True}]
        elif self.path.endswith('/websites/acme/search'):
            data['data'] = {'items': [{'id': 7}]}
        elif self.path.endswith('/websites/dns/search'):
            data['data'] = {'items': [{'id': 8, 'name': 'test-dns'}]}
        elif '/apps/detail/' in self.path:
            data['data'] = {'id': 10}
        elif self.path.endswith('/apps/mysql') or self.path.endswith('/apps/openresty'):
            data['data'] = {'id': 9, 'versions': ['8.0.0']}
        elif self.path.endswith('/search'):
            data['data'] = {'total': 1, 'items': [{'id': 42, 'name': 'test-resource'}]}
        if self.server.fail:
            data = {'message': TOKEN + ' unauthorized'}
        wire = json.dumps(data).encode()
        self.send_response(401 if self.server.fail else 200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(wire)))
        self.end_headers()
        try:
            self.wfile.write(wire)
        except (BrokenPipeError, ConnectionResetError):
            pass


class Client:
    def __init__(self, host, access, timeout=None):
        self.directory = tempfile.TemporaryDirectory(prefix='1panel-test-')
        data = Path(self.directory.name)
        digest = hashlib.sha256(Path(BINARY).read_bytes()).hexdigest()
        setup = subprocess.run([sys.executable, str(ROOT / 'scripts/setup_connection.py'), '--data', str(data),
                                '--binary', str(Path(BINARY).resolve()), '--binary-sha256', digest,
                                '--host', host, '--access-level', access, '--token-stdin'],
                               input=TOKEN + '\n', capture_output=True, text=True)
        if setup.returncode:
            raise AssertionError(setup.stderr)
        command = [sys.executable, '-X', 'utf8', str(ROOT / 'scripts/panel_proxy.py'), '--data', str(data)]
        if timeout is not None:
            command = [sys.executable, '-c',
                       "import sys;from pathlib import Path;sys.path.insert(0,sys.argv[1]);import panel_proxy as p;d=Path(sys.argv[2]);c,t=p.load_config(d);sys.exit(p.serve(c,t,d,timeout=float(sys.argv[3])))",
                       str(ROOT / 'scripts'), str(data), str(timeout)]
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, encoding='utf-8')
        self.messages = queue.Queue()
        threading.Thread(target=self.reader, daemon=True).start()
        self.serial = 0

    def reader(self):
        for line in self.process.stdout:
            self.messages.put(json.loads(line))

    def send(self, value):
        self.process.stdin.write(json.dumps(value) + '\n')
        self.process.stdin.flush()

    def request(self, method, params=None, identity=None):
        self.serial += 1
        identity = self.serial if identity is None else identity
        self.send({'jsonrpc': '2.0', 'id': identity, 'method': method, 'params': params or {}})
        try:
            response = self.messages.get(timeout=12)
        except queue.Empty:
            raise AssertionError('No response; process exit=' + str(self.process.poll())) from None
        if response['id'] != identity:
            raise AssertionError('Response ID changed')
        return response

    def initialize(self):
        response = self.request('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                                              'clientInfo': {'name': 'integration-test', 'version': '1'}}, 'init-string-id')
        if 'error' in response:
            raise AssertionError(response)
        self.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        return response

    def call(self, name, args=None):
        return self.request('tools/call', {'name': name, 'arguments': args or {}})

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        diagnostics = self.process.stderr.read()
        self.process.stdout.close()
        self.process.stderr.close()
        self.directory.cleanup()
        if TOKEN in diagnostics:
            raise AssertionError('Secret leaked in diagnostics')


@unittest.skipUnless(BINARY, 'Set ONEPANEL_TEST_BINARY to the pinned official executable')
class OfficialIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), PanelHandler)
        self.server.daemon_threads = True
        self.server.requests = []
        self.server.fail = self.server.reflect = False
        self.server.delay = 0
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.clients = []

    def tearDown(self):
        for client in self.clients:
            client.close()
        self.server.shutdown()
        self.server.server_close()

    def client(self, access='readonly', timeout=None):
        client = Client('http://127.0.0.1:' + str(self.server.server_port), access, timeout)
        self.clients.append(client)
        client.initialize()
        return client

    def test_actual_handshake_and_permission_filtered_discovery(self):
        for access, expected in [('readonly', READS), ('readwrite', READS | CREATES), ('full', READS | CREATES | INSTALLS)]:
            result = self.client(access).request('tools/list')['result']
            self.assertEqual({t['name'] for t in result['tools']}, expected)
            self.assertTrue(all(t['inputSchema']['type'] == 'object' for t in result['tools']))

    def test_direct_disallowed_calls_never_reach_panel(self):
        client = self.client()
        for name in ['create_website', 'install_mysql', 'delete_website']:
            self.assertTrue(client.call(name)['result']['isError'])
        self.assertEqual(self.server.requests, [])

    def test_all_reads_and_hashed_authentication(self):
        client = self.client()
        for name in READS:
            response = client.call(name, {'name': 'existing-mysql'} if name == 'list_databases' else {})
            self.assertNotIn('error', response)
            self.assertFalse(response['result'].get('isError', False), name)
        self.assertEqual(len(self.server.requests), 6)
        self.assertTrue(all(r['auth'] and not r['leaked'] for r in self.server.requests))

    def test_creations_and_installs_use_official_api(self):
        client = self.client('full')
        cases = [('create_website', {'domain': 'test.example', 'website_type': 'static'}),
                 ('create_ssl', {'domain': 'test.example', 'provider': 'dnsAccount', 'dns_account_id': 8}),
                 ('create_database', {'database_type': 'mysql', 'database': 'mysql', 'name': 'testdb', 'password': 'TEST-password'}),
                 ('install_mysql', {'name': 'test-mysql', 'version': '8.0.0', 'root_password': 'TEST-password', 'port': 33306}),
                 ('install_openresty', {'name': 'test-web', 'http_port': 8080, 'https_port': 8443})]
        for name, arguments in cases:
            response = client.call(name, arguments)
            self.assertNotIn('error', response)
            self.assertFalse(response['result'].get('isError', False), (name, response))
        paths = [r['path'] for r in self.server.requests]
        for path, count in [('/api/v2/websites', 1), ('/api/v2/websites/ssl', 1), ('/api/v2/databases', 1), ('/api/v2/apps/install', 2)]:
            self.assertEqual(paths.count(path), count)
        self.assertTrue(all(r['auth'] for r in self.server.requests))

    def test_errors_and_key_reflection_are_redacted(self):
        client = self.client()
        self.server.fail = True
        response = client.call('get_system_info')
        self.assertTrue(response['result']['isError'])
        self.assertNotIn(TOKEN, json.dumps(response))
        self.server.fail = False
        self.server.reflect = True
        response = client.call('get_system_info')
        self.assertNotIn(TOKEN, json.dumps(response))
        self.assertIn('[REDACTED]', json.dumps(response))

    def test_timeout_is_unknown_and_never_retried(self):
        client = self.client('readwrite', timeout=1)
        self.server.delay = 2
        response = client.call('create_database', {'database_type': 'mysql', 'database': 'mysql', 'name': 'timeout'})
        self.assertTrue(response['result']['isError'])
        self.assertIn('unknown', response['result']['content'][0]['text'])
        time.sleep(2.1)
        self.assertEqual(sum(r['path'] == '/api/v2/databases' for r in self.server.requests), 1)

    def test_invalid_input_does_not_reach_panel(self):
        response = self.client('readwrite').call('create_website', {'domain': 'test.example', 'website_type': 'unsupported'})
        self.assertTrue(response['result']['isError'])
        self.assertEqual(self.server.requests, [])


if __name__ == '__main__':
    unittest.main()
