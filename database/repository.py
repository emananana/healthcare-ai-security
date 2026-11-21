"""Enterprise/security owner: replace with SQLite behind this same interface.

Only synthetic records. Do not expose this repository directly to the UI.
"""
from shared.models import ProposedAction

class MockRepository:
    def __init__(self):
        self.records = {
            "C001": {"policy": "Synthetic policy P001: Demo Basic, active.",
                     "claims": "Synthetic claim CL001: fictional checkup, pending, $40."},
            "C002": {"policy": "Synthetic policy P002: Demo Plus, active.",
                     "claims": "Synthetic claim CL002: fictional consultation, approved, $60."},
        }

    def read(self, action: ProposedAction) -> str:
        """Called only after authorization; return a customer-scoped record."""
        return self.records.get(action.customer_id, {}).get(action.resource, "No synthetic record found.")


class SQLiteRepository:
    """Customer-scoped read adapter. Authorization MUST happen before calling read."""

    def __init__(self, db_path):
        from pathlib import Path
        self.db_path = Path(db_path)

    def read(self, action: ProposedAction) -> str:
        from database.database import connect
        if action.resource == 'policy':
            query = ('SELECT policy_id, description FROM policies '
                     'WHERE customer_id = ? ORDER BY policy_id')
        elif action.resource == 'claims':
            query = ('SELECT claim_id, description, status, amount_cents FROM claims '
                     'WHERE customer_id = ? ORDER BY claim_id')
        else:
            return 'Unsupported resource.'
        with connect(self.db_path) as connection:
            rows = connection.execute(query, (action.customer_id,)).fetchall()
        if not rows:
            return 'No synthetic record found.'
        if action.resource == 'policy':
            return '\n'.join(
                f"{row['policy_id']}: {row['description']}" 
                for row in rows)
        return '\n'.join(
            f"Synthetic claim {row['claim_id']}: {row['description']}," 
            f"{row['status']}, ${row['amount_cents'] / 100:.2f}." for row in rows
        )
