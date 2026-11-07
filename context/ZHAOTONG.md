# Zhaotong — SQLite and security

**First deliverable:** a small seeded SQLite store with customer-scoped reads and independent authorization. You do not need Groq or React to develop this.

## Start here

Follow [setup in the main context](../PROJECT_CONTEXT.md), create branch `zhaotong/sqlite`, and run the existing tests. Skip Groq configuration.

Read `database/repository.py`, `security/gateway.py`, `security/auth.py`, `security/audit.py`, `shared/models.py`, and the authorization tests in `tests/test_interfaces.py`.

## Part 1 — synthetic SQLite records

Do these steps first, in order:

| File | What to implement |
| --- | --- |
| `database/models.py` | Small SQL schema: synthetic customers, policies and claims. Include customer ownership IDs and foreign-key relationships. |
| `database/database.py` | Connection/schema initialization helpers. Accept an explicit database path, enable foreign keys, and close connections. Avoid a shared connection that fails across FastAPI threads. |
| `database/seed.py` | A repeatable CLI such as `python -m database.seed --db /tmp/cometcare-demo.sqlite3`. Seed fictional C001/C002 records. Re-running it must not duplicate records; do not silently destroy an existing database. |
| `database/repository.py` | Keep `MockRepository` unchanged; add `SQLiteRepository(db_path)` with `read(action) -> str`. Use parameterized queries restricted to the requested resource and customer ID. Keep replies as strings so the existing UI/contracts work. |
| `tests/test_repository.py` | Temporary-database tests for seeding, repeat seeding, policy/claims reads, missing records and unsupported resources. |

These names describe the planned additions, not existing implemented helpers. Your CLI should have `--help` and no side effects on import. Put database files in ignored locations; commit the schema/seed code, not a generated database.

## Part 2 — authorization

In `security/gateway.py`, preserve `authorize(user, action) -> AuthorizationResult`. The current User only has customer_id/display_name, so start with ownership and supported-action checks. Do not invent a role field in shared/models.py independently.

Add `tests/test_security.py` verifying own-policy/claims access, denied cross-customer access, and denied unsupported actions. Also inject your repository and gateway into an `EnterpriseAgent` with a fake blue ALLOW result: a cross-customer request must still be blocked before repository.read runs.

The repository scopes reads; the gateway checks who may request them. A SQLite query returning a row is not authorization. You do not need to edit the enterprise agent to test this injection.

## Test and hand off Parts 1–2

Run `python -m unittest discover -s tests -v`. Once the seed CLI and class exist, seed a temporary demo database and show one policy/claim read, plus a denied cross-customer request through the gateway/enterprise pipeline.

Open a PR with implementation, tests, seed command, DB-path configuration needed, and an example constructing `SQLiteRepository(db_path)`. Eman wires it into `llm/setup.py`. You don't need to edit frontend, API, config.py or other agents.

**Where to see it after wiring:** Member Portal → My Policy / My Claims → retrieve information. Security Lab → Defense Analysis → Traditional authorization. Audit Log shows the flow. Before wiring, the app still reads MockRepository even if your SQLite code exists.

## Part 3 — persistent audit, after the first PR

In `security/audit.py`, preserve the in-memory `AuditLog()` default and add an injectable SQLite-backed implementation. Keep `record(event)` and `list_events() -> list[SecurityEvent]`. Serialize/restore nested dataclasses and optional decisions correctly; include incomplete PENDING events. Add restart/round-trip tests in a temporary DB. Don't log provider credentials.

**Render limitation:** the current free service has ephemeral storage. SQLite can work locally, but persistence across hosted restarts requires Eman to arrange persistent storage or explicitly approve reset/reseed demo behavior. Don't promise hosted durability until it is tested.

## Part 4 — authentication, roles and decoys, later

- `security/auth.py`: plan verified sessions and a small role/access matrix with Eman. Keep DEMO_USERS during current demo integration. The shared team password is not individual customer authentication.
- `security/gateway.py`: add role/least-privilege checks once identity fields/contracts are agreed. Eman connects session identity to the API/UI.
- `database/`: add a separate decoy store and explicit decoy read path. Denial must never fall through to protected records. Coordinate with Eman/Reya before changing event outcomes; current DECEIVE simply blocks.

These are separate follow-up PRs, not prerequisites for your SQLite handoff.

## Final required goals and stretch goals

After Parts 1–4, support Eman's comparison runner with a reproducible synthetic reset/seed, expected access outcomes, and a reliable way to distinguish protected records from decoys. Verify actual exposure rather than assuming ALLOW means a leak. The intentionally unsecured condition belongs only in the isolated experiment runner; do not weaken normal portal authorization.

For the final report, document schema/ownership, verified identity and role checks, least privilege, audit behavior, decoy separation and persistence limitations. Test each independently before integrated smoke checks.

**Stretch goals, in order:** richer synthetic policies/claim histories → more roles and access cases → stronger audit integrity controls → additional decoy variants. Keep simple SQLite and repeatable tests; no new database service or microservices unless the team explicitly chooses them.

## Paste this into Claude or Codex

```text
I am Zhaotong, the database/security owner in CometCare. Read
PROJECT_CONTEXT.md, README.md and context/ZHAOTONG.md; inspect the source.
Implement only Parts 1–2 first: small synthetic SQLite schema/connection
helpers, repeatable seed CLI, and SQLiteRepository(db_path).read(action)->str.
Preserve MockRepository and all shared dataclasses/public signatures.
Use parameterized customer-scoped reads, explicit paths and closed connections
safe for synchronous FastAPI use. Preserve gateway ownership/unsupported-action
checks. Add temporary-DB and independent authorization tests, including a
cross-customer request with blue ALLOW. No LLM or network calls are needed.
Do not edit agents, frontend, API, llm/setup.py or shared models. Do not add
roles/authentication/decoys in this first PR or claim free Render storage is
persistent. Run tests, document the seed command and Eman's injection step.
Do not commit, push, merge or deploy automatically.
```
