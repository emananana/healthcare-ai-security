# Team integration guide

All fixtures and records must remain synthetic. No real credentials or LLM APIs are needed for this milestone. Work on individual branches and submit small pull requests; do not change another teammate's public contract without agreement.

## Vanessa — red agent

Own `agents/red_agent.py` and red-specific tests in a new `tests/test_red_agent.py`.

1. Preserve `RedAgent.generate_attack(context: dict[str, str]) -> Attack` from `shared.models`.
2. Read `context['target_customer_id']` as the simulated target; return the request text in `Attack.message` and a category string in `Attack.category`.
3. For the next mock milestone, add deterministic labeled fixtures only. Coordinate any expanded context fields with the integration developer. Do not call the repository or bypass the enterprise agent.
4. Test that generation returns the existing dataclass and that the requested target is represented correctly. Keep each call bounded to one attack.
5. Hand off fixture descriptions, expected outcomes, test commands, and any proposed configuration in your PR. Future model or adaptive work needs a separately agreed scope.

The UI calls `POST /api/attacks`. The adapter passes your attack through `Orchestrator.run_attack`, which invokes the enterprise agent with `source='red_team'`. No frontend changes should be needed for a compatible replacement.

## Reya — blue agent

Own `agents/blue_agent.py` and blue-specific tests in a new `tests/test_blue_agent.py`.

1. Preserve `BlueAgent.analyze_event(event: SecurityEvent) -> DefenseDecision`.
2. Inspect the event's user, message, proposed action and source. At analysis time, defense and authorization may be `None` and outcome is `PENDING`.
3. Return recommendation `ALLOW`, `BLOCK`, or `DECEIVE`; risk `low`, `medium`, or `high`; and a short reason. Return a decision rather than mutating the event or executing tools.
4. Add deterministic tests for own-record and cross-customer fixtures, including expected recommendation and risk. Coordinate additional detection scenarios with the integration developer.
5. Keep optional taxonomy labels within the existing reason for now or propose a shared schema change for team review. Do not add fields directly to `shared/models.py` independently.

The frontend reads the existing event's `defense` object. ALLOW does not override gateway denial. DECEIVE currently yields BLOCK; implementing decoy execution requires coordination with Zhaotong and the integration developer. Real LLM analysis is outside this adapter milestone.

## Zhaotong — database/security

Own `database/`, `security/`, and dedicated tests such as `tests/test_security.py` and `tests/test_repository.py`.

1. Plan a reproducible synthetic SQLite schema and seed script for customers, policies and claims. Keep real and decoy data distinguishable when decoys are introduced later.
2. Preserve `SecurityGateway.authorize(user: User, action: ProposedAction) -> AuthorizationResult`. Deny cross-customer and unsupported requests independently of blue recommendations.
3. Preserve repository `read(action: ProposedAction) -> str`. Supply a compatible repository implementation for injection into `EnterpriseAgent`; retain the current default implementation until the integration developer wires the replacement.
4. Preserve `AuditLog.record(event)` and `list_events() -> list[SecurityEvent]`. Coordinate durable storage, redaction and error behavior. Tests should use temporary databases and isolated fixtures.
5. Keep `security.auth.DEMO_USERS` available during the demo. Propose a verified-session interface before replacing demo identity selection. The frontend's selected ID is not proof of identity.
6. Test own-record reads, cross-customer denial, unsupported actions, missing records and audit round trips. Hand off initialization instructions and an example dependency-injection setup.

The API does not access storage directly. It resolves IDs against `DEMO_USERS`, then calls the orchestrator. Authentication, durable logs and decoy routing are future integration changes, not implemented by this adapter.

## Frontend/chatbot/API/integration owner

Own `frontend/`, `main.py`, `app.py`, `orchestrator.py`, `agents/enterprise_agent.py`, evaluation, and adapter tests. Maintain HTTP serialization, loading/error behavior, and the guarded execution pipeline. Keep Streamlit runnable while React is introduced. Coordinate all shared schema changes; do not change teammate implementations to accommodate the UI.

## Handoff checklist

- Preserve the current dataclasses and public signatures, including enterprise `source` keyword support.
- Document input, output, failure behavior, fixtures, and any setup in the PR.
- Run `python -m unittest discover -s tests -v` in the installed virtual environment.
- Run `npm ci --prefix frontend` then `npm run build --prefix frontend` for frontend/integration changes.
- Test C001 own policy/claims, a C001 request for C002, and one red fixture. Confirm the same event appears in Blue Team Results and Audit Log.
- Keep generated databases, `.env`, virtual environments, `node_modules`, build output and secrets out of Git.
