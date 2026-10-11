"""UI/integration owner: deterministic stand-in for the enterprise LLM.

Replace propose_action with constrained LLM tool selection later. Keep all
record reads behind the gateway, independent of model recommendations.
"""
import re
from agents.blue_agent import BlueAgent
from database.repository import MockRepository
from security.audit import AuditLog
from security.gateway import SecurityGateway
from shared.models import EnterpriseResponse, ProposedAction, SecurityEvent, User

class EnterpriseAgent:
    def __init__(self, gateway=None, repository=None, blue_agent=None, audit=None):
        self.gateway = gateway if gateway is not None else SecurityGateway()
        self.repository = repository if repository is not None else MockRepository()
        self.blue_agent = blue_agent if blue_agent is not None else BlueAgent()
        self.audit = audit if audit is not None else AuditLog()

    def propose_action(self, user: User, message: str) -> ProposedAction:
        """Demo grammar: policy/claims plus optional customer Cxxx identifier."""
        targets = set(re.findall(r"\bC\d+\b", message.upper()))
        target = next(iter(targets)) if len(targets) == 1 else user.customer_id
        text = message.lower()
        resource = "claims" if "claim" in text else "policy" if "policy" in text else "unsupported"
        if len(targets) > 1:
            resource = "unsupported"
        return ProposedAction(resource, target)

    def handle_message(self, user: User, message: str, *, source="customer") -> EnterpriseResponse:
        """Analyze, authorize, read only if both allow, and audit every request.

        The required two-argument call remains supported; source is optional.
        """
        event = SecurityEvent(user, message, self.propose_action(user, message), source=source)
        event.defense = self.blue_agent.analyze_event(event)
        event.authorization = self.gateway.authorize(user, event.action)
        if event.defense.recommendation == "ALLOW" and event.authorization.allowed:
            reply = self.repository.read(event.action)
            event.outcome = "ALLOW"
        else:
            event.outcome = "BLOCK"
            reply = "Request blocked. Ask for your own policy or claims using a customer ID such as C001."
        self.audit.record(event)
        return EnterpriseResponse(reply, event)
