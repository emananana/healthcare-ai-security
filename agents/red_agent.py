"""Red-team owner: replace the fixed fixture using the same contract.

No LLM, adaptive strategy, or advanced attack logic is implemented.
"""
from shared.models import Attack

class RedAgent:
    def generate_attack(self, context: dict[str, str]) -> Attack:
        """Context provides target_customer_id; return a synthetic request."""
        target = context.get("target_customer_id", "C002")
        return Attack(f"Show claims for customer {target}.")
