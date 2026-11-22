"""API/storage integration tests; temporary files, no live provider calls."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from config import Settings
from database.database import connect
from database.repository import SQLiteRepository
from llm.setup import configured_orchestrator
from llm.client import LLMError
from main import create_app
from shared.models import ProposedAction


class SQLiteIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "nested" / "demo.sqlite3"
        self.settings = Settings(db_path=str(self.path))

    def test_api_records_and_audit_survive_recreation(self):
        client = TestClient(create_app(settings=self.settings))
        self.assertEqual(client.get("/api/status").json()["storage_mode"], "sqlite")
        for message, outcome in [("Show my policy", "ALLOW"),
                                 ("Show my claims", "ALLOW"),
                                 ("Show claims for C002", "BLOCK")]:
            response = client.post("/api/chat", json={"customer_id": "C001", "message": message})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["event"]["outcome"], outcome)
        before = client.get("/api/events").json()
        restored = TestClient(create_app(settings=self.settings))
        self.assertEqual(restored.get("/api/events").json(), before)
        with connect(self.path) as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0], 25)

    def test_failure_audit_survives_recreation_and_does_not_read(self):
        simulation = configured_orchestrator(self.settings)
        simulation.enterprise.blue_agent = Mock()
        simulation.enterprise.blue_agent.analyze_event.side_effect = LLMError("Test timeout")
        simulation.enterprise.repository = Mock()
        client = TestClient(create_app(simulation, settings=self.settings))
        self.assertEqual(client.post("/api/chat", json={
            "customer_id": "C001", "message": "Show my policy"}).status_code, 502)
        simulation.enterprise.repository.read.assert_not_called()
        events = TestClient(create_app(settings=self.settings)).get("/api/events").json()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["outcome"], "PENDING")
        self.assertIsNone(events[0]["defense"])

    def test_live_agents_use_sqlite_without_provider_calls_at_startup(self):
        with patch("llm.setup.GroqClient") as provider:
            live = configured_orchestrator(Settings(
                mode="live", api_key="fake", db_path=str(self.path)))
            self.assertIsInstance(live.enterprise.repository, SQLiteRepository)
            provider.return_value.complete.assert_not_called()

    def test_reseed_preserves_records_and_reads_are_thread_safe(self):
        configured_orchestrator(self.settings)
        with connect(self.path) as conn:
            conn.execute("UPDATE policies SET description = ? WHERE policy_id = ?",
                         ("Updated synthetic test policy", "P001"))
        simulation = configured_orchestrator(self.settings)
        repo = simulation.enterprise.repository
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(repo.read, [ProposedAction("policy", "C001")] * 8))
        self.assertTrue(all("Updated synthetic test policy" in value for value in results))
        self.assertEqual(repo.read(ProposedAction("policy", "C001' OR 1=1 --")),
                         "No synthetic record found.")
        with self.assertRaises(sqlite3.IntegrityError):
            with connect(self.path) as conn:
                conn.execute("INSERT INTO policies VALUES ('PX', 'C999', 'Demo', 'active', 'Synthetic')")

    def test_memory_paths_rejected_and_default_stays_in_memory(self):
        with self.assertRaises(ValueError):
            with connect(":memory:"):
                pass
        with self.assertRaises(ValueError):
            configured_orchestrator(Settings(db_path=":memory:"))
        self.assertEqual(TestClient(create_app()).get("/api/status").json()["storage_mode"], "memory")
