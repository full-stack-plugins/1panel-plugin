import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('panel_proxy', ROOT / 'scripts/panel_proxy.py')
proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proxy)


class PolicyTests(unittest.TestCase):
    def test_readonly_denies_direct_write_and_unknown(self):
        self.assertTrue(proxy.allowed('list_websites', 'readonly'))
        self.assertFalse(proxy.allowed('create_website', 'readonly'))
        self.assertFalse(proxy.allowed('delete_website', 'full'))

    def test_creation_and_installation_are_distinct(self):
        self.assertTrue(proxy.allowed('create_database', 'readwrite'))
        self.assertFalse(proxy.allowed('install_mysql', 'readwrite'))
        self.assertTrue(proxy.allowed('install_mysql', 'full'))

    def test_remote_plaintext_or_url_credentials_rejected(self):
        for host in ['http://panel.example.com:9999', 'https://user:secret@panel.example.com', 'https://panel.example.com/#secret']:
            with self.assertRaises(proxy.ConfigError):
                proxy.validate_host(host)
        proxy.validate_host('http://127.0.0.1:9999')
        proxy.validate_host('https://panel.example.com:9999')

    def test_missing_or_bad_configuration_is_not_silently_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(proxy.ConfigError):
                proxy.load_config(Path(directory))
            Path(directory, 'connection.json').write_text(json.dumps({'access_level': 'admin'}))
            with self.assertRaises(proxy.ConfigError):
                proxy.load_config(Path(directory))

    def test_binary_digest_is_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory, 'server.exe')
            binary.write_bytes(b'changed binary')
            with self.assertRaises(proxy.ConfigError):
                proxy.validate_binary(str(binary), '0' * 64)


if __name__ == '__main__':
    unittest.main()
