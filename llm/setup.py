"""Eman's composition point. Teammates do not need to modify FastAPI."""
from agents.enterprise_agent import EnterpriseAgent
from llm.client import GroqClient
from llm.enterprise import EnterpriseLLM
from orchestrator import Orchestrator


def configured_orchestrator(settings):
    if settings.mode == "mock":
        return Orchestrator()
    client = GroqClient(settings.api_key)
    return Orchestrator(enterprise=EnterpriseAgent(
        llm=EnterpriseLLM(client, settings.enterprise_model)))
