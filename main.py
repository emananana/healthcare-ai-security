"""Local research-console adapter; preserves all simulation module contracts."""
from threading import Lock

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field, field_validator

from orchestrator import Orchestrator
from security.auth import DEMO_USERS


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def nonblank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank")
        return value


class AttackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: str
    target_customer_id: str


def create_app(orchestrator: Orchestrator | None = None) -> FastAPI:
    """Inject a compatible orchestrator for tests or teammate integration.

    One process owns one shared demo log. Restart/reload clears it. A lock
    serializes synchronous simulation calls, including audit snapshots.
    """
    api = FastAPI(title="Healthcare AI Security", version="0.1.0")
    simulation = orchestrator if orchestrator is not None else Orchestrator()
    lock = Lock()
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        allow_credentials=False,
    )

    def demo_user(customer_id: str):
        for user in DEMO_USERS:
            if user.customer_id == customer_id:
                return user
        raise HTTPException(status_code=404, detail="Unknown demo customer")

    @api.get("/api/users")
    def users():
        return jsonable_encoder(DEMO_USERS)

    @api.post("/api/chat")
    def chat(body: ChatRequest):
        user = demo_user(body.customer_id)
        with lock:
            return jsonable_encoder(simulation.chat(user, body.message))

    @api.post("/api/attacks")
    def attack(body: AttackRequest):
        user = demo_user(body.customer_id)
        demo_user(body.target_customer_id)
        with lock:
            generated, response = simulation.run_attack(
                user, {"target_customer_id": body.target_customer_id}
            )
            return jsonable_encoder({"attack": generated, "response": response})

    @api.get("/api/events")
    def events():
        with lock:
            return jsonable_encoder(simulation.events())

    return api


app = create_app()
