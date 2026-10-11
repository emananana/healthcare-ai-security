"""Security owner: replace this mock with least-privilege authorization.

Keep authorize(user, action) -> AuthorizationResult. Blue recommendations cannot
bypass this gate. Demo identities are not authenticated sessions.
"""
from shared.models import AuthorizationResult, ProposedAction, User

class SecurityGateway:
    def authorize(self, user: User, action: ProposedAction) -> AuthorizationResult:
        allowed = action.resource in {"policy", "claims"} and user.customer_id == action.customer_id
        return AuthorizationResult(allowed, "Own customer record." if allowed else "Unsupported action or another customer's record.")
