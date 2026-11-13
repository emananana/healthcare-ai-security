
"""Manual live smoke test for the CometCare red agent.

Run from the repository root:
    python -m scripts.smoke_red
"""


from settings import Settings
from agents.red_agent import LiveRedAgent
from llm.client import GroqClient


def main():
    settings = Settings.from_env()

    if not settings.api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    client = GroqClient(settings.api_key)

    agent = LiveRedAgent(
        client=client,
        model=settings.red_model,
    )

    attack = agent.generate_attack({"target_customer_id": "C002"})

    print("Generated attack:")
    print(f"Category: {attack.category}")
    print(f"Message: {attack.message}")


if __name__ == "__main__":
    main()
