"""UI/experiment facade. Inject teammate implementations at this boundary."""
from agents.enterprise_agent import EnterpriseAgent
from agents.red_agent import RedAgent
from llm.client import LLMError
from shared.models import Attack, EnterpriseResponse, User

class Orchestrator:
    def __init__(self, enterprise=None, red=None):
        self.enterprise = enterprise if enterprise is not None else EnterpriseAgent()
        self.red = red if red is not None else RedAgent()

    def chat(self, user: User, message: str) -> EnterpriseResponse:
        return self.enterprise.handle_message(user, message)

    def run_attack(self, user: User, context: dict[str, str]) -> tuple[Attack, EnterpriseResponse]:
        try:
            attack = self.red.generate_attack(context)
        except LLMError as exc:
            # No generated request exists yet: do not fabricate an audited attack.
            raise LLMError(f"Attack generation failed; no attack was submitted. {exc}") from None
        response = self.enterprise.handle_message(user, attack.message, source="red_team")
        return attack, response

    def events(self):
        return self.enterprise.audit.list_events()
