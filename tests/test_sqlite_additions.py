"""
test_sqlite_additions.py
    - New tests only. Run from repository root with unittest discovery.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from agents.enterprise_agent import EnterpriseAgent
from database.repository import SQLiteRepository
from database.seed import seed_database
from database.database import connect
from evaluation.sqlite_runner import run_sqlite_experiment
from security.audit import SQLiteAuditLog
from shared.models import User, ProposedAction, DefenseDecision, SecurityEvent

class SQLiteAdditionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db_path = Path(self.tmp.name) / 'synthetic.sqlite3'
        seed_database(self.db_path)

    def test_seed_is_repeatable(self):
        seed_database(self.db_path)
        with connect(self.db_path) as conn:
            for table in ('customers', 'policies', 'claims'):
                self.assertEqual(
                    conn.execute(
                        f'SELECT COUNT(*) FROM {table}').fetchone()[0], 25)

    def test_repository_filters_customer_and_handles_other_resources(self):
        repo = SQLiteRepository(self.db_path)
        self.assertIn('P001', repo.read(ProposedAction('policy', 'C001')))
        self.assertNotIn('P002', repo.read(ProposedAction('policy', 'C001')))
        self.assertIn('CL002', repo.read(ProposedAction('claims', 'C002')))
        self.assertEqual(repo.read(ProposedAction('policy', 'C999')), 'No synthetic record found.')
        self.assertEqual(repo.read(ProposedAction('unsupported', 'C001')), 'Unsupported resource.')

    def test_cross_customer_blocked_even_if_blue_allows(self):
        repository = Mock()
        blue = Mock()
        blue.analyze_event.return_value = DefenseDecision('ALLOW', 'low', 'test')
        result = EnterpriseAgent(repository=repository, blue_agent=blue).handle_message(
            User('C001', 'Demo'), 'Show claims for C002')
        self.assertEqual(result.event.outcome, 'BLOCK')
        repository.read.assert_not_called()

    def test_audit_round_trip(self):
        audit = SQLiteAuditLog(self.db_path)
        event = SecurityEvent(User('C001', 'Demo'), 'my policy', ProposedAction('policy', 'C001'))
        audit.record(event)
        saved = SQLiteAuditLog(self.db_path).list_events()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0], event)

    def test_evaluation(self):
        report = run_sqlite_experiment(self.db_path)
        self.assertEqual(report['metrics']['total'], 8)
        self.assertEqual(report['metrics']['accuracy'], 1.0)

if __name__ == '__main__':
    unittest.main()
