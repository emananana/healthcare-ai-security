"""Stable integration contracts. Coordinate schema changes with all four teammates."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

Decision = Literal["ALLOW", "BLOCK", "DECEIVE"]
Resource = Literal["policy", "claims", "unsupported"]

@dataclass(frozen=True)
class User:
    customer_id: str
    display_name: str

@dataclass(frozen=True)
class Attack:
    message: str
    category: str = "cross_customer_request"

@dataclass(frozen=True)
class ProposedAction:
    resource: Resource
    customer_id: str

@dataclass(frozen=True)
class DefenseDecision:
    recommendation: Decision
    risk: Literal["low", "medium", "high"]
    reason: str

@dataclass(frozen=True)
class AuthorizationResult:
    allowed: bool
    reason: str

@dataclass
class SecurityEvent:
    user: User
    message: str
    action: ProposedAction
    source: Literal["customer", "red_team"] = "customer"
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    defense: DefenseDecision | None = None
    authorization: AuthorizationResult | None = None
    outcome: Literal["PENDING", "ALLOW", "BLOCK"] = "PENDING"

@dataclass(frozen=True)
class EnterpriseResponse:
    message: str
    event: SecurityEvent
