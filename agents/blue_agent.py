"""Blue-team owner: replace the deterministic rule with an LLM detector.

Keep analyze_event(event) -> DefenseDecision. This is a mock, not a detector
of prompt injection. DECEIVE is reserved; orchestration blocks it for now.
"""
from shared.models import DefenseDecision, SecurityEvent

class BlueAgent:
    def analyze_event(self, event: SecurityEvent) -> DefenseDecision:
        if event.action.customer_id != event.user.customer_id:
            return DefenseDecision("BLOCK", "high", "Mock rule: cross-customer request.")
        return DefenseDecision("ALLOW", "low", "Mock rule: no cross-customer target.")
