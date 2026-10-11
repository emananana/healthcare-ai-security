"""Security owner: replace in-memory audit storage with durable, redacted logs."""
from copy import deepcopy
from shared.models import SecurityEvent

class AuditLog:
    def __init__(self):
        self._events: list[SecurityEvent] = []

    def record(self, event: SecurityEvent) -> None:
        self._events.append(deepcopy(event))

    def list_events(self) -> list[SecurityEvent]:
        return deepcopy(self._events)
