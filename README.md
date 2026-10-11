# Healthcare AI Security — synthetic simulation scaffold

A four-person university project studying red-team and blue-team interaction with a fictional insurance assistant. **Every record is synthetic.** This version is a deterministic, in-memory demonstration: it makes no LLM calls, requires no API keys, and connects to no healthcare systems.

## Run locally

Use Python 3.10 or newer. From this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`. No `.env` file is required. `.env.example` documents the future configuration boundary; environment-file loading is not implemented. Keep future keys in environment variables or ignored secrets files.

Run checks and a baseline experiment without installing Streamlit:

```bash
python3 -m unittest discover -s tests -v
python3 -m evaluation.runner
```

## Demo

Select C001 or C002 in the sidebar. Ask `Show my policy` or `Show my claims`. As C001, try `Show claims for C002`: the request is blocked. The Red Team panel generates the same kind of fixed cross-customer fixture. Blue Team shows recommendations; Security/Audit Log shows actions, authorization, final outcomes, timestamps, and event IDs. Experiment Results runs four labeled fixtures on a fresh orchestrator.

The sidebar is a **demo identity selector, not authentication**. The tabs are a research console, not a production customer interface. Audit data is intentionally visible across demo identities; chat histories are separated by identity. Data and history are session-local and disappear when the session is reset. The parser supports only policy/claim requests and optional explicit IDs such as C002; it does not understand arbitrary natural language or establish a prompt-injection defense.

## Architecture and request flow

```text
Streamlit UI / experiment runner
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
