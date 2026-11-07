# Healthcare AI Security — synthetic simulation scaffold

A four-person university project studying red-team and blue-team interaction with a fictional insurance assistant. **Every record is synthetic.** This version is a deterministic, in-memory demonstration: it makes no LLM calls, requires no API keys, and connects to no healthcare systems.

## React + FastAPI demo (primary UI)

Use Python 3.10+ and Node.js 22.12+ (Node 24 also works). From the repository root, install and run the backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host localhost --port 8000
```

In a second terminal, from the repository root:

```bash
npm ci --prefix frontend
npm run dev --prefix frontend
```

Open **http://localhost:5173**. FastAPI's interactive API docs are at **http://localhost:8000/docs**. Use these exact hostnames: development CORS permits only `http://localhost:5173`, not `127.0.0.1`, other ports, or wildcard origins. Vite uses a strict port so it will report an occupied port instead of silently switching. The API client URL is defined in `frontend/src/api.js`.

Select C001, send `Show my policy`, then `Show claims for C002`. Run a fixed attack in Red Team and inspect Blue Team Results and Audit Log. The frontend retains chat per demo identity until page reload; audit events are shared by all clients of one API process. Use Refresh to see other clients' events. Restarting or reloading the backend clears its in-memory data. Run one backend worker for this demo. Streamlit has a separate in-memory simulation; its events do not appear in React.

This remains a local research console with synthetic records and no authentication. The adapter accepts only known demo IDs, not arbitrary User objects. CORS is a browser development setting, not access control. No LLM APIs, credentials, or environment files are used.

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

### Checks

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
python -m evaluation.runner
npm run build --prefix frontend
```

`tests/test_interfaces.py` remains unchanged. `tests/test_api.py` exercises real mock-module chat/attack/audit integration, validation, independent app state, and limited CORS. The frontend build emits ignored `frontend/dist/`. Use the Vite dev server for the documented CORS setup; preview/production hosting is not configured here.

See [TEAM_GUIDE.md](TEAM_GUIDE.md) for individual work items for Vanessa (red), Reya (blue), and Zhaotong (database/security). The integration owner maintains `frontend/`, `main.py`, and API tests alongside the existing UI/orchestration files. All teammate-owned modules and shared dataclasses are preserved.

## Streamlit fallback

Use Python 3.10 or newer. From this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`. No `.env` file is required. `.env.example` documents the future configuration boundary; environment-file loading is not implemented. Keep future keys in environment variables or ignored secrets files.

After installing requirements, run the full checks and a baseline experiment:

```bash
python3 -m unittest discover -s tests -v
python3 -m evaluation.runner
```

## Demo

Select C001 or C002 in the sidebar. Ask `Show my policy` or `Show my claims`. As C001, try `Show claims for C002`: the request is blocked. The Red Team panel generates the same kind of fixed cross-customer fixture. Blue Team shows recommendations; Security/Audit Log shows actions, authorization, final outcomes, timestamps, and event IDs. Experiment Results runs four labeled fixtures on a fresh orchestrator.

The sidebar is a **demo identity selector, not authentication**. The tabs are a research console, not a production customer interface. Audit data is intentionally visible across demo identities; chat histories are separated by identity. Data and history are session-local and disappear when the session is reset. The parser supports only policy/claim requests and optional explicit IDs such as C002; it does not understand arbitrary natural language or establish a prompt-injection defense.

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

## GitHub and team workflow

Repository: https://github.com/emananana/healthcare-ai-security

This downloaded folder has been connected to the existing repository history, with `origin` pointing to GitHub and local `main` tracking `origin/main`. No scaffold commit or push was made automatically.

Check and publish your work from VS Code's terminal:

```bash
git status
git remote -v
git switch -c integration/scaffold
git add .
git commit -m "Add modular synthetic security simulation scaffold"
git push -u origin integration/scaffold
```

Then open a pull request into `main` on GitHub. VS Code's Source Control panel will also show the changes. If pushing requests authentication, use VS Code's GitHub sign-in or an approved Git credential manager; GitHub does not accept an account password for HTTPS Git pushes. Never paste a token into code or a remote URL. Remote read access was checked; authenticated write access must be established when pushing.

Each teammate should create a separate branch, own the files listed above, and agree on shared dataclass changes together. Pull the latest main before starting a branch, run tests before pushing, and integrate through small pull requests.
