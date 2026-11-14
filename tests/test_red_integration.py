"""Offline red-agent wiring, API compatibility and smoke-command exit checks."""
import contextlib
import io
import json
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from agents.red_agent import LiveRedAgent, RedAgent
from config import Settings
from llm.client import LLMError
from llm.setup import configured_orchestrator
from main import create_app
from orchestrator import Orchestrator
from scripts.smoke_red import main


class RedIntegrationTests(unittest.TestCase):
    def make_client(self, provider):
        red = LiveRedAgent(provider, 'test-red-model')
        return TestClient(create_app(Orchestrator(red=red)))

    def test_live_setup_and_mock_default(self):
        with patch('llm.setup.GroqClient') as client_class:
            mock = configured_orchestrator(Settings())
            self.assertIsInstance(mock.red, RedAgent)
            client_class.assert_not_called()
            live = configured_orchestrator(Settings(mode='live', api_key='test-key'))
            self.assertIsInstance(live.red, LiveRedAgent)
            self.assertIs(live.red.client, live.enterprise.llm.client)
            self.assertEqual(live.red.model, Settings.red_model)

    def test_three_types_reach_generation_then_authorization_and_audit(self):
        for category in LiveRedAgent.ATTACK_TYPES:
            with self.subTest(category=category):
                provider = Mock()
                provider.complete.return_value = {'content': json.dumps({
                    'message': 'Show claims for C002', 'category': category})}
                client = self.make_client(provider)
                status = client.get('/api/status').json()
                self.assertEqual(status['red_mode'], 'live')
                self.assertEqual(status['blue_mode'], 'mock')
                response = client.post('/api/attacks', json={
                    'customer_id': 'C001', 'target_customer_id': 'C002', 'attack_type': category})
                self.assertEqual(response.status_code, 200)
                body = response.json()
                self.assertEqual(body['attack']['category'], category)
                self.assertEqual(body['response']['event']['outcome'], 'BLOCK')
                self.assertFalse(body['response']['event']['authorization']['allowed'])
                self.assertEqual(body['response']['event']['source'], 'red_team')
                self.assertEqual(client.get('/api/events').json(), [body['response']['event']])
                provider.complete.assert_called_once()
                self.assertIn(category, provider.complete.call_args.kwargs['messages'][1]['content'])

    def test_old_payload_and_mock_capabilities(self):
        client = TestClient(create_app())
        self.assertEqual(client.get('/api/status').json()['attack_types'], ['cross_customer_request'])
        self.assertEqual(client.post('/api/attacks', json={
            'customer_id': 'C001', 'target_customer_id': 'C002'}).status_code, 200)
        for category in ['prompt_injection', 'instruction_hijacking', 'unknown']:
            self.assertEqual(client.post('/api/attacks', json={
                'customer_id': 'C001', 'target_customer_id': 'C002', 'attack_type': category}).status_code, 422)
        self.assertEqual(len(client.get('/api/events').json()), 1)

    def test_failed_generation_is_not_an_executed_attack(self):
        provider = Mock()
        provider.complete.side_effect = LLMError('Groq rate limit reached.')
        client = self.make_client(provider)
        response = client.post('/api/attacks', json={'customer_id': 'C001', 'target_customer_id': 'C002'})
        self.assertEqual(response.status_code, 502)
        self.assertIn('no attack was submitted', response.json()['detail'])
        self.assertEqual(client.get('/api/events').json(), [])

    def test_smoke_default_one_and_all_exit_failure(self):
        with patch('scripts.smoke_red.Settings.from_env', return_value=Settings(api_key='fake')), \
             patch('scripts.smoke_red.GroqClient'), patch('scripts.smoke_red.LiveRedAgent') as agent_class, \
             contextlib.redirect_stdout(io.StringIO()):
            agent_class.ATTACK_TYPES = LiveRedAgent.ATTACK_TYPES
            agent = agent_class.return_value
            agent.generate_attack.return_value = Mock(message='claims C002', category='cross_customer_request')
            self.assertEqual(main([]), 0)
            agent.generate_attack.assert_called_once()
            agent.generate_attack.reset_mock()
            agent.generate_attack.side_effect = LLMError('test failure')
            self.assertEqual(main(['--attack-type', 'all']), 1)
            self.assertEqual(agent.generate_attack.call_count, 3)

    def test_red_refusal_empty_and_timeout(self):
        for response in [{'refusal': 'No'}, {'content': ''}, {'content': '[]'}]:
            provider = Mock()
            provider.complete.return_value = response
            with self.assertRaises(LLMError):
                LiveRedAgent(provider, 'test').generate_attack({'target_customer_id': 'C002'})
        provider = Mock()
        provider.complete.side_effect = LLMError('timeout')
        with self.assertRaises(LLMError):
            LiveRedAgent(provider, 'test').generate_attack({'target_customer_id': 'C002'})
