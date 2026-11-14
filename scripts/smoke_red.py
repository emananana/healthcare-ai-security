"""Explicit live generation check: python -m scripts.smoke_red [--attack-type all]."""
import argparse

from config import Settings
from agents.red_agent import LiveRedAgent
from llm.client import GroqClient, LLMError


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate synthetic attacks using Groq (consumes quota).")
    parser.add_argument('--attack-type', choices=[*LiveRedAgent.ATTACK_TYPES, 'all'],
                        default='cross_customer_request')
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if not settings.api_key:
        raise RuntimeError("GROQ_API_KEY is not configured.")
    agent = LiveRedAgent(GroqClient(settings.api_key), settings.red_model)
    attack_types = list(LiveRedAgent.ATTACK_TYPES) if args.attack_type == 'all' else [args.attack_type]
    failed = False
    for attack_type in attack_types:
        print(f"\nTesting generation only: {attack_type}")
        try:
            attack = agent.generate_attack({'target_customer_id': 'C002', 'attack_type': attack_type})
            print(f"Category: {attack.category}\nMessage: {attack.message}")
        except LLMError as error:
            failed = True
            print(f"FAILED: {error}")
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
