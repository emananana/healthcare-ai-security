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
