"""Shared-demo access checks; no network/provider calls."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from config import Settings
from main import create_app


class HostingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / 'frontend' / 'dist').mkdir(parents=True)
        (root / 'frontend' / 'dist' / 'index.html').write_text('<h1>CometCare test</h1>')
        with patch('main.__file__', str(root / 'main.py')):
            self.client = TestClient(create_app(settings=Settings(
                hosted=True, team_password='test-password-123456')))
        self.auth = ('cometcare', 'test-password-123456')

    def test_gate_covers_site_api_docs_and_health_is_public(self):
        self.assertEqual(self.client.get('/healthz').status_code, 200)
        for path in ['/', '/api/users', '/api/events', '/api/status', '/docs', '/openapi.json']:
            self.assertEqual(self.client.get(path).status_code, 401)
            self.assertEqual(self.client.get(path, auth=self.auth).status_code, 200)
        self.assertEqual(self.client.get('/api/users', auth=('cometcare', 'wrong')).status_code, 401)
        self.assertEqual(self.client.get('/', headers={'Authorization': 'Basic invalid'}).status_code, 401)
        self.assertIn('CometCare test', self.client.get('/', auth=self.auth).text)

    def test_same_origin_and_shared_limit(self):
        body = {'customer_id': 'C001', 'message': 'my policy'}
        denied = self.client.post('/api/chat', auth=self.auth, json=body, headers={'Origin': 'https://evil.example'})
        self.assertEqual(denied.status_code, 403)
        for _ in range(10):
            self.assertEqual(self.client.post('/api/chat', auth=self.auth, json=body,
                                             headers={'Origin': 'http://testserver'}).status_code, 200)
        self.assertEqual(self.client.post('/api/chat', auth=self.auth, json=body).status_code, 429)
        self.assertEqual(len(self.client.get('/api/events', auth=self.auth).json()), 10)

    def test_missing_password_rejected(self):
        with self.assertRaises(ValueError):
            create_app(settings=Settings(hosted=True))
