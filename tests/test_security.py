import unittest
from unittest.mock import Mock

from agents.enterprise_agent import EnterpriseAgent
from security.gateway import SecurityGateway
from shared.models import(
    User,
    ProposedAction,
    DefenseDecision,
)

class TestTraditionalSecurity(unittest.TestCase):
    def setUp(self):
        self.gateway = SecurityGateway()
        self.user = User("C001", "Demo Customer")

    def test_own_policy_allowed(self):
        action = ProposedAction("policy", "C001")
        result = self.gateway.authorize(self.user, action)

        self.assertTrue(result.allowed)

    def test_own_claims_allowed(self):
        action = ProposedAction("claims", "C001")
        result = self.gateway.authorize(self.user, action)

        self.assertTrue(result.allowed)

    def test_other_customer_blocked(self):
        action = ProposedAction("claims", "C002")
        result = self.gateway.authorize(self.user, action)

        self.assertFalse(result.allowed)

    def test_unsupported_resource_blocked(self):
        action = ProposedAction("unsupported", "C001")
        result = self.gateway.authorize(self.user, action)

        self.assertFalse(result.allowed)

    def test_blue_allow_cannot_override_gateway(self):
        repository = Mock()
        blue_agent = Mock()

        blue_agent.analyze_event.return_value = (
            DefenseDecision("ALLOW", "low", "test")
        )

        agent = EnterpriseAgent(
            repository=repository,
            gateway=self.gateway,
            blue_agent=blue_agent,
        )

        response = agent.handle_message(
            self.user,
            "Show claims for C002"
        )

        self.assertEqual(response.event.outcome, "BLOCK")
        repository.read.asser_not_called()

    def test_blue_block_prevents_read(self):
        repository = Mock()
        blue_agent = Mock()

        blue_agent.analyze_event.return_value = (
            DefenseDecision("BLOCK", "high", "test")
        )

        agent = EnterpriseAgent(
            repository=repository,
            gateway=self.gateway,
            blue_agent=blue_agent,
        )

        response = agent.handle_message(
            self.user,
            "Show my policy",
        )

        self.assertEqual(response.event.outcome, "BLOCK")
        repository.read.assert_not_called()

if __name__ == "__main__":
    unittest.main()