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

class SQLiteAuditLog:
    def __init__(self, db_path):
        from pathlib import Path
        from database.database import initialize_database
        self.db_path = Path(db_path)
        initialize_database(self.db_path)

    def record(self, event: SecurityEvent) -> None:
        import json
        from dataclasses import asdict
        from database.database import connect
        payload = json.dumps(asdict(event))
        with connect(self.db_path) as connection:
            connection.execute(
                'INSERT INTO audit_events(event_id, timestamp, event_json) VALUES (?, ?, ?)',
                (event.event_id, event.timestamp, payload),
            )

    def list_events(self) -> list[SecurityEvent]:
        import json
        from database.database import connect
        from shared.models import (User, ProposedAction, DefenseDecision, AuthorizationResult)
        
        with connect(self.db_path) as connection:
            rows = connection.execute(
                'SELECT event_json FROM audit_events ORDER BY timestamp, event_id'
            ).fetchall()

        events = []
        for row in rows:
            data = json.loads(row['event_json'])
            data['user'] = User(**data['user'])
            data['action'] = ProposedAction(**data['action'])
            if data.get('defense') is not None:
                data['defense'] = DefenseDecision(**data['defense'])
            if data.get('authorization') is not None:
                data['authorization'] = AuthorizationResult(**data['authorization'])
            events.append(SecurityEvent(**data))
        return events

