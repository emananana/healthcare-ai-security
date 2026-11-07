"""Adapter integration checks using the unchanged simulation implementation."""
import unittest
from fastapi.testclient import TestClient
from main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())

    def test_users_chat_attack_and_audit(self):
        users = self.client.get('/api/users').json()
        self.assertEqual([u['customer_id'] for u in users], ['C001', 'C002'])
        for resource, record in [('policy', 'P001'), ('claims', 'CL001')]:
            response = self.client.post('/api/chat', json={
                'customer_id': 'C001', 'message': f'Show my {resource}'})
            self.assertEqual(response.status_code, 200)
            self.assertIn(record, response.json()['message'])
            self.assertEqual(response.json()['event']['outcome'], 'ALLOW')
        attack = self.client.post('/api/attacks', json={
            'customer_id': 'C001', 'target_customer_id': 'C002'})
        self.assertEqual(attack.status_code, 200)
        event = attack.json()['response']['event']
        self.assertEqual(event['source'], 'red_team')
        self.assertEqual(event['defense']['recommendation'], 'BLOCK')
        self.assertFalse(event['authorization']['allowed'])
        self.assertEqual(event['outcome'], 'BLOCK')
        events = self.client.get('/api/events').json()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[-1], event)
        self.assertEqual(TestClient(create_app()).get('/api/events').json(), [])

    def test_cross_customer_chat_is_blocked(self):
        response = self.client.post('/api/chat', json={
            'customer_id': 'C002', 'message': 'Show policy for C001'})
        self.assertEqual(response.json()['event']['outcome'], 'BLOCK')
        self.assertNotIn('P001', response.json()['message'])

    def test_invalid_requests_do_not_execute(self):
        for message in ['', '   ', 'x' * 4001]:
            self.assertEqual(self.client.post('/api/chat', json={
                'customer_id': 'C001', 'message': message}).status_code, 422)
        self.assertEqual(self.client.post('/api/chat', json={
            'customer_id': 'unknown', 'message': 'my policy'}).status_code, 404)
        self.assertEqual(self.client.post('/api/chat', json={
            'customer_id': 'C001', 'message': 'my policy', 'user': {}}).status_code, 422)
        self.assertEqual(self.client.post('/api/attacks', json={
            'customer_id': 'C001', 'target_customer_id': 'unknown'}).status_code, 404)
        self.assertEqual(self.client.get('/api/events').json(), [])

    def test_cors_is_limited_to_vite(self):
        for origin, expected in [('http://localhost:5173', 200), ('https://example.com', 400)]:
            response = self.client.options('/api/chat', headers={
                'Origin': origin, 'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'content-type'})
            self.assertEqual(response.status_code, expected)
            self.assertEqual(response.headers.get('access-control-allow-origin'),
                             origin if expected == 200 else None)
