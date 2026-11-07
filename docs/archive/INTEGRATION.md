> **Archived planning reference — not the current task list.** Use the [README](../../README.md) for current team instructions.

# Integration reference

Optional technical reference. Start with the [README](../../README.md) and your section in the [team guide](TEAM_GUIDE.md).

## Architecture and request flow

```text
React -> FastAPI / Streamlit UI / experiment runner
              |
         Orchestrator <--- RedAgent.generate_attack(context)
              |
    EnterpriseAgent.handle_message(user, message)
              |
        propose_action (mock parser; future constrained LLM)
              |
        BlueAgent.analyze_event(event)
              |
        SecurityGateway.authorize(user, action)
              |
       both allow? ---- no ---> blocked response
              | yes
       MockRepository.read(action)
              |
          AuditLog + EnterpriseResponse
```

The enterprise agent owns the guarded execution pipeline so direct calls to its required interface also enforce authorization. The orchestrator supplies the stable UI/experiment facade and attack entry point. The blue recommendation can restrict access but cannot grant access denied by the gateway. DECEIVE is a reserved contract value and currently blocks access; decoy routing is not implemented.

## Layout and team ownership

| Owner | Files | Responsibility and replacement boundary |
| --- | --- | --- |
| Enterprise environment/security | `security/auth.py`, `security/gateway.py`, `security/audit.py` | Replace demo users with verified sessions; enforce least privilege; persist/redact audit events. |
| Enterprise environment/security | `database/repository.py`, `database/database.py`, `database/models.py`, `database/seed.py` | Replace in-memory records with SQLite, migrations/schema and synthetic seeding; eventually add decoys. Preserve repository `read(action) -> str`. |
| Red-team developer | `agents/red_agent.py` | Replace fixed fixture while keeping `generate_attack(context) -> Attack`. No advanced or adaptive logic is included. |
| Blue-team developer | `agents/blue_agent.py` | Replace cross-customer rule with analysis, risk classification and optional ATT&CK/ATLAS metadata agreed by the team. |
| UI/integration/evaluation | `app.py`, `orchestrator.py`, `agents/enterprise_agent.py` | Maintain UI and orchestration; later replace parser/response generation with a constrained enterprise LLM. |
| UI/integration/evaluation | `evaluation/runner.py`, `evaluation/metrics.py` | Maintain labeled scenarios, experiments and metrics. |
| Shared by team | `shared/models.py`, `tests/test_interfaces.py` | Agree on contract changes before implementation; run regression checks. |

`tools/` contains reserved adapters, not active tool execution. `config.py` is reserved configuration. `evaluation/scenarios.json` is an empty future external-scenario placeholder; the current runner explicitly defines its four fixtures in Python.

## Integration contracts

Shared dataclasses are defined in `shared/models.py`:

- `User(customer_id, display_name)`: identity supplied by the trusted session boundary in the eventual implementation.
- `Attack(message, category)`: generated synthetic input.
- `ProposedAction(resource, customer_id)`: scoped read request; resources are policy, claims or unsupported.
- `DefenseDecision(recommendation, risk, reason)`: ALLOW/BLOCK/DECEIVE and low/medium/high risk.
- `AuthorizationResult(allowed, reason)`: independent access-control result.
- `SecurityEvent`: user, message, proposed action, source, ID, UTC timestamp, decisions and outcome.
- `EnterpriseResponse(message, event)`: assistant reply and its auditable result.

Required public methods:

```python
RedAgent.generate_attack(context: dict[str, str]) -> Attack
BlueAgent.analyze_event(event: SecurityEvent) -> DefenseDecision
SecurityGateway.authorize(user: User, action: ProposedAction) -> AuthorizationResult
EnterpriseAgent.handle_message(user: User, message: str) -> EnterpriseResponse
```

`context` currently uses `target_customer_id`. The enterprise method additionally accepts optional keyword `source="customer"` (`"red_team"` for attack runs). Keep it when replacing the entire enterprise implementation. The audit object implements `record(event)` and `list_events()`. The orchestrator exposes `chat(user, message)`, `run_attack(user, context)`, and `events()`.

Modules can be replaced without UI edits through dependency injection:

```python
enterprise = EnterpriseAgent(
    gateway=SecurityGateway(),
    repository=MockRepository(),
    blue_agent=BlueAgent(),
    audit=AuditLog(),
)
orchestrator = Orchestrator(enterprise=enterprise, red=RedAgent())
```

Import these classes from their owning modules. Substitute compatible teammate implementations at construction. All calls are synchronous. Preserve return types, accepted values and method signatures. The current mocks do not have network/provider failures; exception handling and failure audit policy must be added when external services are integrated. Never let an LLM call unrestricted storage or treat a blue ALLOW as authorization.

## Evaluation

The baseline contains own-policy and own-claims requests labeled ALLOW and two cross-customer requests labeled BLOCK. Accuracy is correct outcomes / all cases. Attack block rate is blocked malicious cases / malicious cases. False positive rate is blocked legitimate cases / legitimate cases. Empty denominators return 0.0; inspect `total` before interpreting results. These fixture scores only validate wiring and do not demonstrate real security effectiveness.

Tests cover contracts, own-record reads, independent gateway enforcement even when blue allows, BLOCK/DECEIVE handling, ambiguous/unsupported inputs, audit recording and metrics. SQLite, authentication, LLMs, prompt-injection detection, adaptive attacks, durable logs and decoy responses remain teammate work.


### HTTP integration contracts

`main.py` imports the unchanged `Orchestrator`. `create_app(orchestrator=...)` supports replacement/injection for integration tests. Synchronous calls are serialized with a process-local lock. FastAPI's `jsonable_encoder` recursively serializes the existing dataclasses, including nested events and optional decisions; domain models are not duplicated.

| Endpoint | Request | Response / existing method |
| --- | --- | --- |
| `GET /api/users` | None | Array of `User` objects from `security.auth.DEMO_USERS` |
| `POST /api/chat` | `{"customer_id":"C001","message":"Show my policy"}` | Serialized `EnterpriseResponse` from `Orchestrator.chat(user, message)` |
| `POST /api/attacks` | `{"customer_id":"C001","target_customer_id":"C002"}` | `{"attack": Attack, "response": EnterpriseResponse}` from `Orchestrator.run_attack(user, context)` |
| `GET /api/events` | None | Array of `SecurityEvent` objects from `Orchestrator.events()` |

Chat messages must be nonblank and at most 4,000 characters. Unknown demo IDs return 404; malformed input and extra request fields return 422. A valid simulated blocked request returns HTTP 200 with `event.outcome="BLOCK"`, because the simulation executed successfully. Adapter validation failures never invoke the simulation or create a security event. Blue results come from `event.defense`; authorization and final outcome remain separate. Unexpected module failures return server errors, not fabricated ALLOW results. The existing core does not yet audit exceptions.

The frontend shows loading and error states, disables duplicate submissions while busy, and times requests out after 15 seconds. A timeout does not cancel server execution; refresh the audit before retrying. React renders record text without raw HTML.


## Local state and development setup

Use `http://localhost:5173` for React and `http://localhost:8000` for FastAPI. CORS permits only that Vite origin. Run one API worker: its in-memory log is shared across browsers, and backend reloads clear it. Browser refresh clears chat history. No environment file or API key is needed.

Policy and claims are returned as text, not structured insurance records. The UI does not invent missing coverage or claim fields. The current parser supports policy/claim requests and explicit IDs such as C002; it is not a general-purpose LLM.

## Additional checks

With the virtual environment activated:

```bash
python -m evaluation.runner
npm run build --prefix frontend
```

The baseline scores validate wiring only, not real-world defense effectiveness.

## Older Streamlit fallback

The main interface is CometCare in React. If needed, the original UI is still available:

```bash
source .venv/bin/activate
streamlit run app.py
```

Its session-local events are separate from the FastAPI log. Its older tab names differ from CometCare's navigation.
