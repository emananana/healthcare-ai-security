# Your part of CometCare

Start the app using the [README](README.md), then read your section below. **Write your code in VS Code; use CometCare to observe the results.** The frontend is already connected to your module.

The tasks below are your immediate starting points. **[ROADMAP.md](ROADMAP.md)** lays out the full proposal, including working LLMs, dependencies, adaptation, deception, evaluation, and hosting. A working three-LLM demonstration is a required milestone, not a stretch goal.

## Vanessa — generate the simulated request

**Open:** [agents/red_agent.py](agents/red_agent.py).

**Today:** it returns one fixed request for another customer's claims.

**First task:** add and test a small set of deterministic synthetic attack fixtures. Start by testing the current fixture, then agree with the integration owner how additional fixtures will be selected. Keep one generated attack per call; do not change the API yourself.

**Keep this interface:**

```python
RedAgent.generate_attack(context) -> Attack
```

The context contains `target_customer_id`. Return the existing `Attack` dataclass with `message` and `category`. Your module generates text; the existing orchestrator sends it to the enterprise assistant.

**See your work:** Security Lab → **Attack Simulator** → **Run simulated attack**. Look for your generated prompt and the assistant's response. Then open Defense Analysis to see how it was handled.

**Hand off:** your module, red-specific tests, example requests, and expected outcomes. You do not need to edit React or the database.

## Reya — analyze the request

**Open:** [agents/blue_agent.py](agents/blue_agent.py).

**Today:** it checks whether the requested customer differs from the requesting customer.

**First task:** test legitimate and cross-customer requests, then develop your detection logic behind the same method. Start with deterministic cases so the team can verify decisions before adding an LLM.

**Keep this interface:**

```python
BlueAgent.analyze_event(event) -> DefenseDecision
```

Read the event's user, message, action, and source. Return a recommendation (`ALLOW`, `BLOCK`, or `DECEIVE`), risk (`low`, `medium`, or `high`), and reason. At this point, authorization has not run yet. Do not execute database actions or mutate the event.

**See your work:** run an attack, then open Security Lab → **Defense Analysis** → **Blue-team recommendation**. Normal member requests also trigger your analysis automatically. There is no separate blue-team button.

The neighboring **Traditional authorization** result belongs to Zhaotong. Your ALLOW cannot override his denial. DECEIVE currently blocks; actual decoy responses require coordinated integration later.

**Hand off:** your module, blue-specific tests, and examples showing expected recommendation/risk/reason. Coordinate new output fields before changing shared models.

## Zhaotong — provide records and enforce access

**Start with:** [database/repository.py](database/repository.py) and [security/gateway.py](security/gateway.py). You also own the other files in `database/` and `security/`.

**Today:** records are stored in memory; the gateway only allows supported reads of the requesting customer's own records.

**First task:** build a small synthetic SQLite store and a repeatable seed script. Keep the existing repository interface, then test that the gateway still denies other-customer access. Coordinate wiring the SQLite implementation with the integration owner.

**Keep these interfaces:**

```python
repository.read(action) -> str
SecurityGateway.authorize(user, action) -> AuthorizationResult
AuditLog.record(event)
AuditLog.list_events() -> list[SecurityEvent]
```

Keep `security.auth.DEMO_USERS` available until we agree on authentication changes. Preserve the existing shared dataclasses. Add tests using temporary databases so tests do not affect demo data.

**See your work:**

- Member Portal → **My Policy / My Claims** → retrieve a record.
- Security Lab → **Defense Analysis** → **Traditional authorization**.
- Security Lab → **Audit Log** → recorded events.

Test both own-record access and cross-customer denial, including when blue recommends ALLOW. Plan authentication, persistent audit storage, and decoys as subsequent steps.

**Hand off:** implementation, seed/setup commands, tests, and any instructions needed to activate the new repository.

## Eman — connect everything

Own `frontend/`, `main.py`, `orchestrator.py`, `agents/enterprise_agent.py`, evaluation, and API tests. Keep the UI connected, integrate compatible teammate modules, and coordinate shared contract changes. `app.py` is the older Streamlit fallback; teammates can ignore it for the main CometCare workflow.

## How to deliver your work

1. Start from an updated, clean `main`, then create your own branch, for example `git switch -c vanessa/red-fixtures` (use a name appropriate to your task).
2. Edit your assigned module and add its tests. Preserve the current method arguments and return types.
3. In the activated virtual environment, run `python -m unittest discover -s tests -v`.
4. Try your behavior in CometCare using the paths above. Python saves reload the backend and clear its in-memory events.
5. Commit and push your branch, then open a pull request into `main`. Explain what changed, how to test it, and any setup needed. The integration owner helps connect it.

Everyone runs a separate local copy. You see a teammate's work after it is merged and you pull it—not simply because they saved their file.

Keep all records synthetic and secrets out of Git. If you need exact fields or API details, use the [integration reference](docs/INTEGRATION.md); you do not need to read it all before starting.
