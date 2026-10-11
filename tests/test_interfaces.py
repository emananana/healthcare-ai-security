"""Contract and authorization regression checks; no API or Streamlit required."""
import unittest
from unittest.mock import Mock
from agents.blue_agent import BlueAgent
from agents.enterprise_agent import EnterpriseAgent
from agents.red_agent import RedAgent
from evaluation.metrics import calculate_metrics
from evaluation.runner import run_experiment
from security.auth import DEMO_USERS
from security.gateway import SecurityGateway
from shared.models import Attack, DefenseDecision, ProposedAction, SecurityEvent

class InterfaceTests(unittest.TestCase):
    def test_red_contract(self):
        attack = RedAgent().generate_attack({"target_customer_id": "C002"})
        self.assertIsInstance(attack, Attack)
        self.assertIn("C002", attack.message)

    def test_blue_contract(self):
        event = SecurityEvent(DEMO_USERS[0], "claims", ProposedAction("claims", "C002"))
        self.assertEqual(BlueAgent().analyze_event(event).recommendation, "BLOCK")

    def test_authorization_contract(self):
        gateway = SecurityGateway()
        self.assertTrue(gateway.authorize(DEMO_USERS[0], ProposedAction("policy", "C001")).allowed)
        self.assertFalse(gateway.authorize(DEMO_USERS[0], ProposedAction("claims", "C002")).allowed)
        self.assertFalse(gateway.authorize(DEMO_USERS[0], ProposedAction("unsupported", "C001")).allowed)

    def test_enterprise_contract_and_own_records(self):
        agent = EnterpriseAgent()
        for user, policy, claim in ((DEMO_USERS[0], "P001", "CL001"), (DEMO_USERS[1], "P002", "CL002")):
            self.assertIn(policy, agent.handle_message(user, "my policy").message)
            self.assertIn(claim, agent.handle_message(user, "my claims").message)
        self.assertEqual(len(agent.audit.list_events()), 4)

    def test_blue_allow_cannot_bypass_security(self):
        repository = Mock()
        blue = Mock()
        blue.analyze_event.return_value = DefenseDecision("ALLOW", "low", "test")
        agent = EnterpriseAgent(repository=repository, blue_agent=blue)
        response = agent.handle_message(DEMO_USERS[0], "claims for C002")
        self.assertEqual(response.event.outcome, "BLOCK")
        repository.read.assert_not_called()
        self.assertEqual(agent.audit.list_events()[0].outcome, "BLOCK")

    def test_blue_block_and_deceive_prevent_reads(self):
        for decision in ("BLOCK", "DECEIVE"):
            with self.subTest(decision=decision):
                repository, blue = Mock(), Mock()
                blue.analyze_event.return_value = DefenseDecision(decision, "high", "test")
                response = EnterpriseAgent(repository=repository, blue_agent=blue).handle_message(DEMO_USERS[0], "my policy")
                self.assertEqual(response.event.outcome, "BLOCK")
                repository.read.assert_not_called()

    def test_ambiguous_and_unsupported_requests(self):
        agent = EnterpriseAgent()
        for message in ("hello", "claims for C001 and C002"):
            self.assertEqual(agent.handle_message(DEMO_USERS[0], message).event.outcome, "BLOCK")

    def test_experiment_and_empty_metrics(self):
        report = run_experiment()
        self.assertEqual(report["metrics"]["total"], 4)
        self.assertEqual(report["metrics"]["accuracy"], 1.0)
        self.assertEqual(report["metrics"]["false_positive_rate"], 0.0)
        self.assertEqual(calculate_metrics([])["total"], 0)

if __name__ == "__main__":
    unittest.main()
