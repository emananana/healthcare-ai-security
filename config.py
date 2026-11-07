"""Eman's server-only configuration. Mock mode is the safe, offline default."""
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    mode: str = "mock"
    hosted: bool = False
    team_password: str = field(default="", repr=False)
    api_key: str = field(default="", repr=False)
    enterprise_model: str = "openai/gpt-oss-20b"
    red_model: str = "qwen/qwen3.8-27b"
    blue_model: str = "openai/gpt-oss-120b"

    @classmethod
    def from_env(cls):
        mode = os.getenv("COMETCARE_MODE", "mock").strip().lower()
        if mode not in {"mock", "live"}:
            raise ValueError("COMETCARE_MODE must be mock or live")
        settings = cls(
            mode=mode,
            hosted=os.getenv("COMETCARE_HOSTED", "false").lower() == "true",
            team_password=os.getenv("TEAM_PASSWORD", ""),
            api_key=os.getenv("GROQ_API_KEY", "").strip(),
            enterprise_model=os.getenv("ENTERPRISE_MODEL", cls.enterprise_model),
            red_model=os.getenv("RED_MODEL", cls.red_model),
            blue_model=os.getenv("BLUE_MODEL", cls.blue_model),
        )
        if mode == "live" and not settings.api_key:
            raise ValueError("Live mode requires GROQ_API_KEY in the server environment")
        if settings.hosted and len(settings.team_password) < 16:
            raise ValueError("Hosted mode requires TEAM_PASSWORD with at least 16 characters")
        return settings
