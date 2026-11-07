# Reya — blue agent

**Your first deliverable:** an independently testable live LLM detector that returns a valid defense decision.

## Start here

1. Follow [setup in the main context](../PROJECT_CONTEXT.md), create branch `reya/blue-llm`, and run the tests.
2. Read `agents/blue_agent.py`, `shared/models.py`, `llm/client.py`, and `test_blue_contract` in `tests/test_interfaces.py`.
3. Use your own local Groq key and `settings.blue_model`, which differs from red's model.

## Build in this order

1. **Keep `BlueAgent()` as the offline mock.** Add `LiveBlueAgent(client, model)` in `agents/blue_agent.py`, preserving `analyze_event(event) -> DefenseDecision`. This class is a planned deliverable.
2. Give the model the request, user ID, proposed resource/target and policy: customers may request only their own policy/claims. Delimit the request as untrusted content, not detector instructions. At analysis time the event may have no defense/authorization yet and outcome is PENDING.
3. Ask for structured recommendation/risk/reason. Validate against ALLOW/BLOCK/DECEIVE and low/medium/high; return the existing `DefenseDecision`. Start with ALLOW/BLOCK cases. Never query records or execute actions.
4. Handle provider failures and invalid output with `LLMError`, not a fabricated ALLOW or successful detection. Do not mutate the supplied event.
5. Add `tests/test_blue_agent.py` with fake-client replies. Add explicit `scripts/smoke_blue.py`, guarded by `if __name__ == '__main__'`, that constructs a benign and a malicious event and prints your live decisions. No calls on import.

## Test before handing off

- C001 asks for C001 policy: benign fixture.
- C001 asks for C002 claims: malicious fixture.
- Include a benign message with suspicious-looking words and a message attempting to instruct the detector to allow it.
- Check allowed field values, invalid/missing output and timeouts/rate limits.
- Confirm the input event is unchanged and default tests remain offline.

Run `python -m unittest discover -s tests -v`. After creating the script, run `python -m scripts.smoke_blue` from the repo root with your key. It makes explicit live calls; responses are evidence to review, not guaranteed classifications. You don't need Vanessa's generator or SQLite.

## Where the result appears

After Eman connects it: run a chat request or attack, then open **Security Lab → Defense Analysis → Blue-team recommendation**. There is no blue run button; analysis is automatic. **Traditional authorization** is Zhaotong's independent check. Final outcome is the enterprise pipeline's result, not your classification. DECEIVE currently blocks until decoy routing is implemented.

## Send to Eman

Push your branch, open a PR and include tests, examples, model and smoke command. Eman selects your class in `llm/setup.py`, updates the mode label and error handling, then merges/deploys. The shared server uses **its existing Groq key**; you don't send yours. A branch push alone doesn't activate your live model.

**Later:** better detection evaluation, justified MITRE labels and DECEIVE recommendations connected to isolated dummy records.

## Remaining required goals — in implementation order

1. **Complete the first handoff above.** Verify your actual recommendation/risk/reason appears in Defense Analysis after Eman wires the class. Keep classification separate from the authorization and final outcome.
2. **Improve labeled detection tests.** Work with Vanessa's scenario descriptions, including benign requests and false-positive traps. Use separate development and held-out cases. Map relevant cases to MITRE ATT&CK/ATLAS with sources and rationale.
3. **Analyze integrated/adaptive requests.** Once Eman connects a bounded campaign, inspect each supplied event. Do not own the attack loop or assume access to earlier context that is not provided.
4. **Add DECEIVE recommendations.** Define and test the policy with Eman/Zhaotong. Your module returns a decision only; Zhaotong supplies decoys and Eman routes responses. Until they connect that route, DECEIVE still blocks.
5. **Support evaluation/reporting.** Define how recommendations map to positive/negative detections, review confusion matrices/false positives/negatives, and explain detector limitations. Eman measures detection latency and aggregates results; provider errors are reported separately, not silently labeled threats.

**Stretch goals, in order:** more held-out scenarios → additional defender-model comparisons → calibrated confidence if a schema change is agreed → richer analysis across campaign attempts. Do not add output fields unilaterally.

## Paste this into Claude or Codex

```text
I am Reya, the blue-agent owner in CometCare. Read PROJECT_CONTEXT.md,
README.md, and context/REYA.md, then inspect the source.
Preserve offline BlueAgent() and add LiveBlueAgent(client, model) in
agents/blue_agent.py with analyze_event(event) -> DefenseDecision.
Use the shared injected Groq client. Treat inspected messages as untrusted
content; validate recommendation/risk/reason and return the existing dataclass.
Do not read records, execute actions, mutate events, or silently ALLOW on
provider errors. Add fake-client tests and an explicit scripts/smoke_blue.py
CLI using constructed events. Do not make live calls without asking me or
request secrets in chat. Do not edit shared models, other agents, UI or
composition files. Run offline tests and explain the integration handoff.
Do not commit, push, merge, or deploy automatically.
```
