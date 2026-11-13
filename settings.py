"""Application configuration."""

import os
from dataclasses import dataclass


@dataclass
class Settings:
    mode: str = "mock"
    api_key: str = ""
    enterprise_model: str = "openai/gpt-oss-20b"
    red_model: str = "qwen/qwen3.8-27b"
    blue_model: str = "openai/gpt-oss-120b"

    @classmethod
    def from_env(cls):
        return cls(
            mode=os.getenv("APP_MODE", "mock"),
            api_key=os.getenv("GROQ_API_KEY", ""),
            enterprise_model=os.getenv(
                "ENTERPRISE_MODEL", "openai/gpt-oss-20b"
            ),
            red_model=os.getenv(
                "RED_MODEL", "qwen/qwen3.8-27b"
            ),
            blue_model=os.getenv(
                "BLUE_MODEL", "openai/gpt-oss-120b"
            ),
        )
