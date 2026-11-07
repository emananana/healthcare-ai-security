# Vanessa — red agent

**Your first deliverable:** one real LLM-generated synthetic attack, independently testable. No adaptive loop yet.

## Start here

1. Follow [setup in the main context](../PROJECT_CONTEXT.md), create branch `vanessa/red-llm`, and run the existing tests.
2. Read `agents/red_agent.py`, `shared/models.py`, `llm/client.py`, and the red example in `tests/test_interfaces.py`.
3. Use your own local Groq key. The configured starting model is `settings.red_model`; do not hardcode keys or choose a separate provider.

## Build in this order

1. **Keep `RedAgent()` as the existing offline mock.** In `agents/red_agent.py`, add `LiveRedAgent(client, model)` with `generate_attack(context) -> Attack`. This is the agreed handoff shape, not an existing class.
2. Write a prompt for one synthetic insurance test: cross-customer access, prompt injection, or instruction hijacking. Input `context` currently provides `target_customer_id`. Generate text only; don't read the database, call the enterprise assistant, or execute tools.
3. Call the injected shared client's `complete(model=..., messages=...)`. Require a short structured result, parse/validate `message` and `category`, then return the existing `Attack` dataclass. Don't return raw JSON or a different schema.
4. Handle invalid output/refusals honestly. Propagate safe `LLMError` failures; don't replace a failed live call with a fixed attack and label it live.
5. Add `tests/test_red_agent.py` using a fake client. Add `scripts/smoke_red.py` as a manual CLI guarded by `if __name__ == '__main__'`. It loads Settings/GroqClient, instantiates your live class and prints one synthetic attack. No network calls on import.

## Test before handing off

- Fake provider returns valid output → correct `Attack` fields and target handling.
- Empty/malformed/refusal output → explicit failure, no invented execution success.
- Provider timeout/rate-limit → error handled, no automatic infinite retry.
- Default `RedAgent()` and the original suite still work offline.

Run `python -m unittest discover -s tests -v`. Once you have created the smoke script, run `python -m scripts.smoke_red` from the repository root with your local key. One live call consumes your quota. No React, database or blue LLM is needed.

## Where the result appears

After Eman connects your live class: **Security Lab → Attack Simulator → Run simulated attack**. The generated prompt comes from your model. The assistant response and final outcome come from the integrated pipeline; you do not implement those yourself. Defense Analysis explains the decisions.

## Send to Eman

Push your branch and open a PR. Include files, test results, one sample output, model used and smoke command. Eman selects `LiveRedAgent` in `llm/setup.py`, updates the displayed mode, verifies API errors, then merges/deploys. On Render it uses **the existing server key**, not your local key. Your branch push alone doesn't activate it.

**Later:** bounded feedback-based adaptation and MITRE labels, after one generated attack works end to end.

## Remaining required goals — in implementation order

1. **Complete the first handoff above.** Eman wires your class; verify actual generated text in Attack Simulator and the corresponding audit event. A blocked attack is a valid execution result.
2. **Build a labeled scenario set.** Cover cross-customer requests, prompt injection and instruction hijacking; state an observable objective for each. Keep development examples separate from held-out evaluation examples. Coordinate labels with Reya; do not change her detector.
3. **Add bounded adaptation.** After the integrated flow is stable, generate a next attempt from the allowed earlier response. Eman owns the campaign loop, budgets and cancellation. Agree on a small feedback format before changing context; current values are strings. Do not give the attacker private defender reasoning or unrestricted database contents.
4. **Test the decoy condition.** After Eman/Zhaotong/Reya connect decoys, record attacker-visible behavior without treating returned dummy data as protected-data exposure. Don't assume the attacker was convinced merely because a decoy was returned.
5. **Support evaluation/reporting.** Supply attack labels, justified MITRE mappings with Reya, fixed replay cases and bounded campaigns. Explain success/failure criteria and sample traces. Eman computes aggregate metrics; Zhaotong verifies actual protected-record exposure.

**Stretch goals, in order:** more attack families → synthetic document/indirect injection cases → extra red-model comparisons → larger bounded campaigns. Only after the core comparison works; no attacks against outside systems.

## Paste this into Claude or Codex

```text
I am Vanessa, the red-agent owner in CometCare. Read PROJECT_CONTEXT.md,
README.md, and context/VANESSA.md, then inspect the actual files.
Implement only my first deliverable: preserve offline RedAgent(), and add
LiveRedAgent(client, model) in agents/red_agent.py with the existing
 generate_attack(context) -> Attack contract. Reuse llm.client.GroqClient;
accept an injected client/model, validate output, and generate only one
synthetic insurance attack at a time. Do not execute attacks or query data.
Add fake-client tests and an explicit scripts/smoke_red.py CLI. Do not make
live API calls without asking me, request my key in chat, edit shared models,
change Eman's composition/frontend, or implement adaptive loops yet.
Run the offline tests. Explain changed files, manual smoke steps and what
Eman must wire. Do not commit, push, merge, or deploy automatically.
```
