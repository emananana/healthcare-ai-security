

"""Manual live smoke test for all three red-agent attack types."""

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

    attack_types = [
        "cross_customer_request",
        "prompt_injection",
        "instruction_hijacking",
    ]

    for attack_type in attack_types:
        print("\n" + "=" * 60)
        print(f"Testing: {attack_type}")
        print("=" * 60)

        try:
            attack = agent.generate_attack({
                "target_customer_id": "C002",
                "attack_type": attack_type,
            })

            print(f"Category: {attack.category}")
            print(f"Message: {attack.message}")

        except Exception as error:
            print(f"FAILED: {error}")


if __name__ == "__main__":
    main()

