"""
 test_repository.py
"""

import tempfile
import unittest
from pathlib import Path

from database.database import connect
from database.seed import seed_database
from database.repository import SQLiteRepository
from shared.models import ProposedAction

class TestSQLiteRepository(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.db_path = Path(self.temp_dir.name) / "test.db"
        seed_database(self.db_path)
        self.repo = SQLiteRepository(self.db_path)

    def test_records_created(self):
        with connect(self.db_path) as conn:
            for table in ("customers", "policies", "claims"):
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"
                ).fetchone()[0]

                self.assertEqual(count, 25)

    def test_repeatable_seeding(self):
        seed_database(self.db_path)

        with connect(self.db_path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM customers"
            ).fetchone()[0]

        self.assertEqual(count, 25)

    def test_read_own_policy(self):
        action = ProposedAction("policy", "C001")
        result = self.repo.read(action)

        self.assertIn("P001", result)

    def test_read_own_claims(self):
        action = ProposedAction("claims", "C001")
        result = self.repo.read(action)

        self.assertIn("CL001", result)

    def test_customer_scoping(self):
        action = ProposedAction("claims", "C001")
        result = self.repo.read(action)

        self.assertIn("CL001", result)

    def test_missing_customer(self):
        action = ProposedAction("policy", "C999")
        result = self.repo.read(action)

        self.assertIn("No synthetic record found.", result)

    def test_supported_resource(self):
        action = ProposedAction("unsupported", "C001")
        result = self.repo.read(action)

        self.assertEqual(result, "Unsupported resource.")

if __name__ == "__main__":
    unittest.main()