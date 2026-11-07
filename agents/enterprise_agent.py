"""Eman: guarded enterprise execution with optional live LLM planning.

Default construction remains offline. Inject llm to enable bounded live calls.
Every proposed read passes through the existing blue agent and gateway.
"""
import re
from agents.blue_agent import BlueAgent
from database.repository import MockRepository
from security.audit import AuditLog
from security.gateway import SecurityGateway
from llm.client import LLMError
from shared.models import EnterpriseResponse, ProposedAction, SecurityEvent, User

class EnterpriseAgent:
    def __init__(self, gateway=None, repository=None, blue_agent=None, audit=None, *, llm=None):
        self.llm = llm
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
        event = SecurityEvent(user, message, ProposedAction("unsupported", user.customer_id), source=source)
        transcript = None
        try:
            if self.llm is not None:
                event.action, transcript = self.llm.plan(user, message)
            else:
                event.action = self.propose_action(user, message)
        except LLMError:
            # PENDING means execution did not finish, not a successful blue detection.
            self.audit.record(event)
            raise
        event.defense = self.blue_agent.analyze_event(event)
        event.authorization = self.gateway.authorize(user, event.action)
        if event.defense.recommendation == "ALLOW" and event.authorization.allowed:
            record = self.repository.read(event.action)
            try:
                reply = self.llm.answer(transcript, record) if self.llm is not None else record
            except LLMError:
                # Authorization may be allowed, but no completed response was returned.
                self.audit.record(event)
                raise
            event.outcome = "ALLOW"
        else:
            event.outcome = "BLOCK"
            reply = "Request blocked. Ask for your own policy or claims using a customer ID such as C001."
        self.audit.record(event)
        return EnterpriseResponse(reply, event)
