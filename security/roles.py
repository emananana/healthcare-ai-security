from dataclasses import dataclass, field

@dataclass
class AccessContext:
    user_id: str
    role: str
    assigned_customers: set[str] = field(default_factory=set)

ROLE_PERMISSIONS = {
    "customer": {"policy", "claims"},
    "staff": {"policy", "claims"},
    "admin": {"policy", "claims", "audit"}
}

def authorize_role(
        user: AccessContext,
        resource: str,
        customer_id: str,
) -> bool:
    role = user.role.lower()
    resource = resource.lower()

    if resource not in ROLE_PERMISSIONS.get(role, set()):
        return False

    if role == "admin":
        return True

    if role == "customer":
        return user.user_id.upper() == customer_id.upper()

    if role == "staff":
        return customer_id.upper() in{
            customer.upper()
            for customer in user.assigned_customers
        }

    return False