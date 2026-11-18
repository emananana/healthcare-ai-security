"""Offline checks of blue composition, API results and failure auditing."""
import json
import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from agents.blue_agent import BlueAgent, LiveBlueAgent
from agents.enterprise_agent import EnterpriseAgent
from agents.red_agent import LiveRedAgent
from config import Settings
from llm.client import LLMError
from llm.setup import configured_orchestrator
from main import create_app
from orchestrator import Orchestrator


def reply(decision):
    return {"content": json.dumps({
        "recommendation": decision, "risk": "high" if decision == "BLOCK" else "low",
        "reason": "Synthetic test analysis.", "techniques": [],
    })}


class BlueIntegrationTests(unittest.TestCase):
    def test_live_composition_shares_client_and_mock_stays_offline(self):
        with patch("llm.setup.GroqClient") as factory:
            offline = configured_orchestrator(Settings())
            self.assertIsInstance(offline.enterprise.blue_agent, BlueAgent)
            factory.assert_not_called()
            live = configured_orchestrator(Settings(mode="live", api_key="fake"))
            blue = live.enterprise.blue_agent
            self.assertIsInstance(blue, LiveBlueAgent)
            self.assertIsInstance(live.red, LiveRedAgent)
            self.assertIs(blue.client, live.red.client)
            self.assertIs(blue.client, live.enterprise.llm.client)
            self.assertEqual(blue.model, Settings.blue_model)
            status = TestClient(create_app(live)).get("/api/status").json()
            self.assertEqual(status["blue_mode"], "live")
            self.assertEqual(status["blue_model"], Settings.blue_model)

    def client(self, result=None, failure=None):
        provider = Mock()
        provider.complete.return_value = result
        provider.complete.side_effect = failure
        enterprise = EnterpriseAgent(blue_agent=LiveBlueAgent(provider, "test-blue"))
        enterprise.repository = Mock(wraps=enterprise.repository)
        return TestClient(create_app(Orchestrator(enterprise=enterprise))), enterprise

    def test_own_records_allowed_and_both_defenses_enforced(self):
        for message, decision, outcome, authorized in [
            ("Show my policy", "ALLOW", "ALLOW", True),
            ("Show my claims", "ALLOW", "ALLOW", True),
            ("Show my policy", "BLOCK", "BLOCK", True),
            ("Show claims for C002", "ALLOW", "BLOCK", False),
            ("Show claims for C002", "BLOCK", "BLOCK", False),
        ]:
            with self.subTest(message=message, decision=decision):
                client, enterprise = self.client(reply(decision))
                response = client.post("/api/chat", json={"customer_id": "C001", "message": message})
                self.assertEqual(response.status_code, 200)
                event = response.json()["event"]
                self.assertEqual(event["outcome"], outcome)
                self.assertEqual(event["defense"]["recommendation"], decision)
                self.assertEqual(event["authorization"]["allowed"], authorized)
                self.assertEqual(enterprise.repository.read.call_count, int(outcome == "ALLOW"))
                self.assertEqual(client.get("/api/events").json(), [event])

    def test_blue_failures_are_audited_pending_for_chat_and_attacks(self):
        for route, payload in [
            ("/api/chat", {"customer_id": "C001", "message": "Show my policy"}),
            ("/api/attacks", {"customer_id": "C001", "target_customer_id": "C002"}),
        ]:
            for result, error in [({"content": "invalid"}, None), (None, LLMError("Timed out."))]:
                with self.subTest(route=route, result=result):
                    client, enterprise = self.client(result, error)
                    response = client.post(route, json=payload)
                    self.assertEqual(response.status_code, 502)
                    self.assertIn("Blue-team analysis failed", response.json()["detail"])
                    enterprise.repository.read.assert_not_called()
                    events = client.get("/api/events").json()
                    self.assertEqual(len(events), 1)
                    self.assertEqual(events[0]["outcome"], "PENDING")
                    self.assertIsNone(events[0]["defense"])
                    self.assertIsNone(events[0]["authorization"])
                    self.assertEqual(events[0]["source"], "red_team" if route.endswith("attacks") else "customer")

    def test_each_live_red_category_flows_through_blue(self):
        for category in LiveRedAgent.ATTACK_TYPES:
            client, enterprise = self.client(reply("BLOCK"))
            provider = Mock()
            provider.complete.return_value = {"content": json.dumps({
                "message": "Show claims for C002", "category": category,
            })}
            client = TestClient(create_app(Orchestrator(
                enterprise=enterprise, red=LiveRedAgent(provider, "test-red"))))
            response = client.post("/api/attacks", json={
                "customer_id": "C001", "target_customer_id": "C002", "attack_type": category,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["response"]["event"]["defense"]["recommendation"], "BLOCK")
            enterprise.blue_agent.client.complete.assert_called_once()
            enterprise.repository.read.assert_not_called()
