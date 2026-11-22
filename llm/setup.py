"""Eman's composition point. Teammates do not need to modify FastAPI."""
from agents.enterprise_agent import EnterpriseAgent
from agents.red_agent import LiveRedAgent
from agents.blue_agent import LiveBlueAgent
from llm.client import GroqClient
from llm.enterprise import EnterpriseLLM
from orchestrator import Orchestrator


def configured_orchestrator(settings):
    storage = {}
    if settings.db_path:
        from pathlib import Path
        from database.seed import seed_database
        from database.repository import SQLiteRepository
        from security.audit import SQLiteAuditLog

        if settings.db_path == ":memory:":
            raise ValueError("COMETCARE_DB_PATH must be a file-backed SQLite path")
        path = Path(settings.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        seed_database(path)  # Idempotent: never reset existing records or audit.
        storage = {"repository": SQLiteRepository(path), "audit": SQLiteAuditLog(path)}
    if settings.mode == "mock":
        return Orchestrator(enterprise=EnterpriseAgent(**storage))
    client = GroqClient(settings.api_key)
    return Orchestrator(enterprise=EnterpriseAgent(
        **storage,
        llm=EnterpriseLLM(client, settings.enterprise_model),
        blue_agent=LiveBlueAgent(client, settings.blue_model)),
        red=LiveRedAgent(client, settings.red_model))
