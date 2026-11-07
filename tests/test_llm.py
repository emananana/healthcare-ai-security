"""Offline checks: injected model responses and HTTP transport, never real API calls."""
import json
import os
import unittest
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient

from agents.enterprise_agent import EnterpriseAgent
from config import Settings
from llm.client import GroqClient, LLMError
from llm.enterprise import EnterpriseLLM
from main import create_app
from orchestrator import Orchestrator
from security.auth import DEMO_USERS
from shared.models import DefenseDecision


def tool_reply(target="C001", resource="policy"):
    return {"role": "assistant", "content": None, "tool_calls": [{
        "id": "call_1", "type": "function", "function": {
            "name": "read_insurance_record",
            "arguments": json.dumps({"resource": resource, "customer_id": target}),
        },
    }]}


class EnterpriseLLMTests(unittest.TestCase):
    def make_agent(self, replies):
        client = Mock()
        client.complete.side_effect = replies
        agent = EnterpriseAgent(llm=EnterpriseLLM(client, "test-model"))
        return agent, client

    def test_authorized_tool_then_grounded_answer(self):
        agent, client = self.make_agent([tool_reply(), {"content": "Your synthetic policy is P001."}])
        response = agent.handle_message(DEMO_USERS[0], "my policy")
        self.assertEqual(response.event.outcome, "ALLOW")
        self.assertIn("P001", response.message)
        first = client.complete.call_args_list[0].kwargs
        second = client.complete.call_args_list[1].kwargs
        self.assertNotIn("P001", json.dumps(first))
        self.assertIn("P001", json.dumps(second))
        self.assertNotIn("P002", json.dumps(second))
        self.assertEqual(second["tool_choice"], "none")
        self.assertEqual(len(agent.audit.list_events()), 1)

    def test_cross_customer_denied_even_if_blue_allows(self):
        agent, client = self.make_agent([tool_reply("C002")])
        agent.blue_agent = Mock()
        agent.blue_agent.analyze_event.return_value = DefenseDecision("ALLOW", "low", "test")
        agent.repository = Mock()
        response = agent.handle_message(DEMO_USERS[0], "policy for C002", source="red_team")
        self.assertEqual(response.event.outcome, "BLOCK")
        self.assertEqual(response.event.source, "red_team")
        self.assertFalse(response.event.authorization.allowed)
        agent.repository.read.assert_not_called()
        self.assertEqual(client.complete.call_count, 1)

    def test_blue_block_or_deceive_prevents_reads(self):
        for recommendation in ["BLOCK", "DECEIVE"]:
            agent, client = self.make_agent([tool_reply()])
            agent.blue_agent = Mock()
            agent.blue_agent.analyze_event.return_value = DefenseDecision(recommendation, "high", "test")
            agent.repository = Mock()
            self.assertEqual(agent.handle_message(DEMO_USERS[0], "my policy").event.outcome, "BLOCK")
            agent.repository.read.assert_not_called()
            self.assertEqual(client.complete.call_count, 1)

    def test_malformed_or_multiple_tools_never_read(self):
        unknown = tool_reply(); unknown['tool_calls'][0]['function']['name'] = 'execute_sql'
        malformed = tool_reply(); malformed['tool_calls'][0]['function']['arguments'] = '{'
        extra = tool_reply(); extra['tool_calls'][0]['function']['arguments'] = '{"resource":"policy","customer_id":"C001","sql":"select *"}'
        multiple = tool_reply(); multiple['tool_calls'] *= 2
        for reply in [unknown, malformed, extra, multiple, tool_reply("../C001"), tool_reply(resource="customers")]:
            agent, client = self.make_agent([reply])
            agent.repository = Mock()
            with self.assertRaises(LLMError):
                agent.handle_message(DEMO_USERS[0], "my policy")
            agent.repository.read.assert_not_called()
            self.assertEqual(agent.audit.list_events()[0].outcome, "PENDING")

    def test_no_tool_does_not_return_invented_record(self):
        agent, client = self.make_agent([{"content": "Invented policy XYZ"}])
        agent.repository = Mock()
        response = agent.handle_message(DEMO_USERS[0], "hello")
        self.assertNotIn("XYZ", response.message)
        self.assertEqual(response.event.outcome, "BLOCK")
        agent.repository.read.assert_not_called()

    def test_generation_failure_and_extra_tool_are_not_success(self):
        for final in [LLMError("Provider unavailable"), tool_reply(), {"content": ""}]:
            agent, client = self.make_agent([tool_reply(), final])
            with self.assertRaises(LLMError):
                agent.handle_message(DEMO_USERS[0], "my policy")
            event = agent.audit.list_events()[0]
            self.assertTrue(event.authorization.allowed)
            self.assertEqual(event.outcome, "PENDING")
            self.assertEqual(client.complete.call_count, 2)

    def test_api_returns_safe_error_and_keeps_incomplete_audit(self):
        agent, _ = self.make_agent([LLMError("Groq rate limit reached.")])
        client = TestClient(create_app(Orchestrator(enterprise=agent)))
        response = client.post('/api/chat', json={'customer_id': 'C001', 'message': 'my policy'})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['detail'], 'Groq rate limit reached.')
        self.assertEqual(client.get('/api/events').json()[0]['outcome'], 'PENDING')

    def test_no_cross_request_history(self):
        agent, client = self.make_agent([tool_reply(), {'content': 'P001'}, tool_reply('C002'), {'content': 'P002'}])
        agent.handle_message(DEMO_USERS[0], 'my policy secret marker')
        agent.handle_message(DEMO_USERS[1], 'my policy')
        self.assertNotIn('secret marker', json.dumps(client.complete.call_args_list[2].kwargs))


class ProviderTests(unittest.TestCase):
    def test_api_through_real_helper_with_simulated_http(self):
        requests = []
        def handler(request):
            payload = json.loads(request.content)
            requests.append(payload)
            reply = tool_reply() if len(requests) == 1 else {"role": "assistant", "content": "Synthetic policy P001: Demo Basic, active."}
            finish = "tool_calls" if len(requests) == 1 else "stop"
            return httpx.Response(200, json={"choices": [{"finish_reason": finish, "message": reply}]})
        provider = GroqClient("test-key", transport=httpx.MockTransport(handler))
        enterprise = EnterpriseAgent(llm=EnterpriseLLM(provider, "test-model"))
        client = TestClient(create_app(Orchestrator(enterprise=enterprise),
                                      settings=Settings(mode="live", enterprise_model="test-model")))
        response = client.post("/api/chat", json={"customer_id": "C001", "message": "my policy"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["event"]["outcome"], "ALLOW")
        self.assertIn("P001", response.json()["message"])
        self.assertEqual(len(requests), 2)
        self.assertEqual(client.get("/api/events").json()[0], response.json()["event"])

    def test_http_payload_and_success(self):
        def handler(request):
            self.assertEqual(str(request.url), 'https://api.groq.com/openai/v1/chat/completions')
            payload = json.loads(request.content)
            self.assertEqual(payload['max_completion_tokens'], 1024)
            self.assertEqual(request.headers['Authorization'], 'Bearer test-key')
            return httpx.Response(200, json={'choices': [{'finish_reason': 'stop', 'message': {'role': 'assistant', 'content': 'OK'}}]})
        client = GroqClient('test-key', transport=httpx.MockTransport(handler))
        self.assertEqual(client.complete(model='test-model', messages=[])['content'], 'OK')

    def test_errors_sanitized_without_retries(self):
        for status in [401, 403, 429, 500]:
            calls = []
            def handler(request):
                calls.append(request)
                return httpx.Response(status, text='SECRET provider body')
            client = GroqClient('test-key', transport=httpx.MockTransport(handler))
            with self.assertRaises(LLMError) as caught:
                client.complete(model='test-model', messages=[])
            self.assertNotIn('SECRET', str(caught.exception))
            self.assertEqual(len(calls), 1)

    def test_timeout_and_truncation(self):
        def timeout(request):
            raise httpx.ReadTimeout('secret detail')
        with self.assertRaisesRegex(LLMError, 'timed out'):
            GroqClient('test', transport=httpx.MockTransport(timeout)).complete(model='test', messages=[])
        for body in [{}, {'choices': []}, {'choices': [{'finish_reason': 'length', 'message': {'role': 'assistant'}}]}]:
            client = GroqClient('test', transport=httpx.MockTransport(lambda request: httpx.Response(200, json=body)))
            with self.assertRaises(LLMError):
                client.complete(model='test', messages=[])

    def test_configuration_and_status_do_not_expose_keys(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Settings.from_env().mode, 'mock')
        with patch.dict(os.environ, {'COMETCARE_MODE': 'live', 'GROQ_API_KEY': ''}, clear=True):
            with self.assertRaises(ValueError): Settings.from_env()
        with patch.dict(os.environ, {'COMETCARE_MODE': 'typo'}, clear=True):
            with self.assertRaises(ValueError): Settings.from_env()
        settings = Settings(mode='live', api_key='test-secret')
        self.assertNotIn('test-secret', repr(settings))
        response = TestClient(create_app(settings=settings)).get('/api/status')
        self.assertEqual(response.json()['enterprise_mode'], 'live')
        self.assertEqual(response.json()['blue_mode'], 'mock')
        self.assertNotIn('test-secret', response.text)

if __name__ == '__main__':
    unittest.main()
