"""Isolated comparison semantics and failure accounting; no network calls."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from fastapi.testclient import TestClient
from config import Settings
from evaluation.comparison import run_case, SCENARIOS
from llm.client import LLMError
from main import create_app
from shared.models import DefenseDecision

class ComparisonTests(unittest.TestCase):
    def test_exposure_and_legitimate_success(self):
        for scenario in SCENARIOS:
            rows = run_case(scenario["id"], "mock", Settings())["results"]
            self.assertEqual(len(rows), 3)
            if scenario["malicious"]:
                self.assertEqual([r["unauthorized_exposure"] for r in rows], [True, False, False])
                self.assertEqual([r["outcome"] for r in rows], ["ALLOW", "BLOCK", "BLOCK"])
            else:
                self.assertTrue(all(r["legitimate_success"] for r in rows))
            self.assertIsNone(rows[0]["blue_recommendation"])

    def test_live_detector_one_call_and_gateway_independence(self):
        detector = Mock()
        detector.analyze_event.return_value = DefenseDecision("ALLOW", "low", "Missed attack")
        rows = run_case("cross_customer", "live", Settings(), detector=detector)["results"]
        detector.analyze_event.assert_called_once()
        self.assertEqual(rows[2]["outcome"], "BLOCK")
        self.assertFalse(rows[2]["unauthorized_exposure"])
        self.assertEqual(rows[2]["blue_recommendation"], "ALLOW")

    def test_detector_errors_remain_unknown_not_blocked(self):
        detector = Mock()
        detector.analyze_event.side_effect = LLMError("Simulated rate limit")
        row = run_case("cross_customer", "live", Settings(), detector=detector)["results"][2]
        self.assertEqual(row["outcome"], "PENDING")
        self.assertIsNone(row["unauthorized_exposure"])
        self.assertIsNotNone(row["error"])

    def test_false_positive_separate_from_authorization(self):
        detector = Mock()
        detector.analyze_event.return_value = DefenseDecision("BLOCK", "high", "False positive")
        row = run_case("own_policy", "live", Settings(), detector=detector)["results"][2]
        self.assertTrue(row["authorization_allowed"])
        self.assertFalse(row["legitimate_success"])

    def test_api_validation_and_portal_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            client = TestClient(create_app(settings=Settings(db_path=str(Path(directory)/"portal.sqlite3"))))
            self.assertEqual(len(client.get("/api/experiments").json()["scenarios"]), 6)
            for payload in [{"scenario_id":"unknown"}, {"scenario_id":"own_policy", "mode":"live"},
                            {"scenario_id":"own_policy", "gateway":"disabled"}]:
                self.assertEqual(client.post("/api/experiments/case", json=payload).status_code, 422)
            self.assertEqual(client.post("/api/experiments/case", json={"scenario_id":"cross_customer"}).status_code, 200)
            self.assertEqual(client.get("/api/events").json(), [])
            response = client.post("/api/chat", json={"customer_id":"C001", "message":"Show claims for C002"})
            self.assertEqual(response.json()["event"]["outcome"], "BLOCK")
