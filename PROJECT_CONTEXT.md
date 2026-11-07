# Project context & roadmap

**This is the shared plan.** Read the short roadmap, then your personal context file. Setup and technical details are expandable below; you do not need to read everything to start.

| Your part | Your context, tasks and coding-assistant prompt |
| --- | --- |
| Vanessa — red agent | [context/VANESSA.md](context/VANESSA.md) |
| Reya — blue agent | [context/REYA.md](context/REYA.md) |
| Zhaotong — database/security | [context/ZHAOTONG.md](context/ZHAOTONG.md) |
| Eman — chatbot/integration | [context/EMAN.md](context/EMAN.md) |

## What we are studying

Can an LLM defender plus traditional access controls protect a fictional insurance assistant from an opposing LLM attacker? We test synthetic prompt injection, instruction hijacking and attempts to get another fictional customer's records. We also test deceptive responses containing isolated dummy records.

The system uses React, FastAPI, Python agents and eventually SQLite. No real healthcare data or external attack targets. CometCare is not an official UT Dallas service.

## What works now

Eman's enterprise Groq chatbot and shared Render app are working, as tested by Eman. Red and blue are still fixed mocks; records and audit are in memory. The team login protects the shared research console but is not individual customer authentication. DECEIVE currently blocks; actual decoys, adaptation and full research metrics are still to build.

Shared app: **https://healthcare-ai-security.onrender.com/**. Username `cometcare`; Eman provides the password privately. Its code comes from deployed `main`, not unmerged branches. Free hosting can sleep and current data resets on restart.

## How to test before everyone is finished

Cloning this repository includes Eman's enterprise chatbot. You can run it locally in live mode with your own key; you do not need to connect to Eman's laptop or Render.

- **Vanessa:** test that her live generator returns a valid attack for a supplied target. Later, run that attack through the local enterprise assistant with the mock blue agent still in place.
- **Reya:** use hand-written SecurityEvent examples such as “C001 requests C002's claims.” A detector accepts an event regardless of whether a human, fixture or red LLM produced its text. Test her live detector directly; no live red agent is needed.
- **Zhaotong:** test a temporary SQLite database and fixed user/action pairs without any LLM.

Offline unit tests use fake provider replies to check code behavior; explicit live smoke checks test actual models. These checks do not establish real-world detection accuracy. Eman then connects each completed module to the local app and runs end-to-end checks before merging/deploying. The current app will keep using mock red/blue until that wiring is added.

## Roadmap — implement in this order

| Stage | Goal | Work and dependency | Ready when |
| --- | --- | --- | --- |
| 1. Independent modules | Each teammate's first working component | Vanessa: one live attack; Reya: one live analysis; Zhaotong: seeded SQLite + ownership checks. All can work in parallel with fixtures. Eman's enterprise LLM already works. | Each module has offline tests and a runnable example. |
| 2. First integrated LLM demo | Live red → enterprise → blue → authorization → response | Eman wires and reviews each module as it arrives; no need to wait for all three. Mock storage can remain until SQLite is ready. | Real model outputs appear in the app; legitimate requests work and cross-customer access is checked. |
| 3. Secured enterprise | SQLite, verified identity, roles, least privilege and durable audit | Zhaotong builds components; Eman connects API/session identity and chooses a hosted persistence plan. | Own-record access succeeds; cross-customer denial holds even when blue allows; audit survives a restart where persistence is configured. |
| 4. Proposal behaviors | Bounded adaptation and isolated deception | Vanessa designs next-attempt generation; Eman supplies bounded feedback/loop. Reya decides when to DECEIVE; Zhaotong supplies decoys; Eman routes explicitly. These two tracks can proceed in parallel after Stage 3. | A short campaign uses earlier feedback and stops; a decoy response never leaks protected records. |
| 5. Evaluation | Compare unsecured, traditional, AI-assisted, and deception conditions | Vanessa supplies attack objectives; Reya supplies labels/MITRE mappings; Zhaotong verifies protected/decoy outcomes; Eman runs/exports comparisons. | Repeated, reproducible experiments and honest metrics, including errors. |
| 6. Final demonstration | Explain results and limitations | Everyone writes their component's explanation; Eman assembles the demonstration/report. | Another teammate can reproduce a legitimate request, attack, defense and decoy example. |

**Working red/blue LLMs are required, not stretch goals.** Stages 3–5 also cover core proposal commitments, at a small controlled scale. Do not start every stage at once.

For Stage 5, replay the same held-out labeled requests across conditions; evaluate adaptive campaigns separately with matched objectives/budgets. Measure actual unauthorized exposure, blue detection accuracy, false positives, detection time and correct legitimate-task completion. ALLOW alone is not success. Record model/configuration, errors and denominators; keep intentionally unsecured experiments out of the public portal. Use relevant MITRE ATT&CK/ATLAS labels with source links and justification.

**Stretch goals, after the core:** more model comparisons, larger campaigns, indirect injection through synthetic documents, richer deception analysis, stronger statistical analysis, and live progress/results visualizations. Individual priorities are in each person's file.

## How independent work becomes the shared app

1. Create your own branch before editing; use the fixed inputs in your personal context file.
2. Build and test your module locally. You do not need another person's finished module.
3. Push your branch and open a pull request. Include code, tests, an example, and setup notes.
4. **Eman reviews, wires, and merges it.** Shared contract changes are coordinated through Eman.
5. Render deploys `main`; Eman verifies the live result. Now everyone sees it at the shared URL.

A branch push alone does not enable a live agent. Current setup still selects mock red/blue; Eman must explicitly select new implementations and update the UI mode labels. Local development can test those implementations directly before that wiring exists.

## One Groq setup

| Component | Current configured starting model |
| --- | --- |
| Eman's enterprise assistant | `openai/gpt-oss-20b` |
| Vanessa's red agent | `qwen/qwen3.8-27b` |
| Reya's blue agent | `openai/gpt-oss-120b` |

These are configuration choices, not a promise every account has access. Eman coordinates changes; red and blue must remain different models. Use the existing helper in `llm/client.py` rather than building separate provider infrastructure.

**Locally:** Vanessa/Reya use their own Groq keys for explicit live checks. Zhaotong needs no key. **On Render:** all integrated agents use the server's existing key; teammates never send their personal keys to Eman. Visitors need only the team login. Keep automated tests offline with fake provider replies; rate limits/refusals are not successful defenses.

<details>
<summary><strong>Setup, local Groq, app startup and branch commands</strong></summary>

#### Local setup

The shared website is for viewing integrated work. Your local checkout is where you develop. Python 3.10+ is needed; Node.js 22.12+ is only needed for the frontend.

### 1. Clone and create your branch before editing

```bash
git clone https://github.com/emananana/healthcare-ai-security.git
cd healthcare-ai-security
git switch -c vanessa/red-llm
```

Use your own branch name: `reya/blue-llm`, `zhaotong/sqlite`, or `eman/integration`. Already cloned? Save unfinished work first, then `git switch main`, `git pull origin main`, and create your new branch. Do not reuse `git switch -c` for a branch that already exists; use `git switch branch-name`.

### 2. Install Python dependencies and run the existing tests

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Windows PowerShell: use `python` instead of `python3` and `.venv\Scripts\Activate.ps1` instead of `source ...`. All these tests are offline. Keep them passing. Each new terminal needs virtual-environment activation.

### 3. Vanessa/Reya: configure your own Groq key for manual live checks

Create your own key at https://console.groq.com/keys. Do not ask Eman for her key. In your Mac/Linux terminal:

```bash
export COMETCARE_MODE=live
read -s GROQ_API_KEY
```

Press Enter after the command, then paste the key at the hidden prompt and press Enter again. Keep the name `GROQ_API_KEY` literally in the command. Then:

```bash
export GROQ_API_KEY
```

On PowerShell, use hidden input and set it for this terminal only:

```powershell
$key = Read-Host 'Groq API key' -AsSecureString
$env:GROQ_API_KEY = [System.Net.NetworkCredential]::new('', $key).Password
$env:COMETCARE_MODE = 'live'
Remove-Variable key
```

These values apply only to that terminal and its child processes. `.env.example` documents configuration but `.env` is not auto-loaded. Never commit or paste a key into an AI assistant. The ordinary test suite stays offline even when you have a key; run live smoke scripts separately.

Zhaotong: skip this section. SQLite/security tests need no Groq key.

### 4. Optional: run the local app

Backend terminal:

```bash
python -m uvicorn main:app --reload --host localhost --port 8000
```

Second terminal, from the repo root:

```bash
npm ci --prefix frontend
npm run dev --prefix frontend
```

Open http://localhost:5173/. Default mode is mock. With live environment variables, the enterprise assistant uses Groq. **The current setup still selects mock red/blue agents. Adding a live class alone will not change the app.** Use your personal smoke script first; Eman connects the live implementation and updates mode labels during integration.

Try C001 → `Show my policy`, then `Show claims for C002`. Security Lab → Attack Simulator runs red; Defense Analysis shows blue and separate authorization results; Audit Log records events. Saving Python may reload the backend and clear the current in-memory log.

### 5. Test, push your branch, and ask Eman to review

After implementing the tasks in your guide:

```bash
python -m unittest discover -s tests -v
git status
```

Stage only your intended files. Example for Vanessa (adjust filenames for your role):

```bash
git add agents/red_agent.py tests/test_red_agent.py scripts/smoke_red.py
git commit -m "Add live red agent with offline tests"
git push -u origin vanessa/red-llm
```

The example test/script files are deliverables you create; they do not exist yet. On GitHub, open a pull request with base `main` and your branch as compare. Include what changed, test results, one synthetic example, and setup instructions. Do not merge directly: **Eman reviews, wires the component, and merges**. Successful Render deployment makes it visible on the shared site. Pushing your branch alone does not.

</details>

<details>
<summary><strong>Technical contracts — for implementation or your coding assistant</strong></summary>

### Stable contracts

Use the dataclasses in shared/models.py; do not redefine them:

- RedAgent.generate_attack(context: dict[str, str]) -> Attack(message, category). Current context: target_customer_id.
- BlueAgent.analyze_event(event: SecurityEvent) -> DefenseDecision(recommendation, risk, reason).
- Recommendations: ALLOW/BLOCK/DECEIVE; risk: low/medium/high.
- SecurityGateway.authorize(user, action) -> AuthorizationResult(allowed, reason).
- Repository.read(action: ProposedAction) -> str; action has resource (policy/claims/unsupported) and customer_id.
- AuditLog.record(event); list_events() -> list[SecurityEvent].
- EnterpriseAgent.handle_message(user, message, *, source='customer') -> EnterpriseResponse(message, event).
- Orchestrator.chat, run_attack, events are used by FastAPI. Existing HTTP payloads must remain compatible.

Every record read requires blue ALLOW and independent gateway authorization. DECEIVE currently blocks. Live enterprise execution allows one validated read and at most two provider calls; no shared conversation memory. Provider failures return HTTP 502; incomplete events use existing PENDING outcome. Do not report errors/refusals as successful defenses.

### Independence and composition

Keep RedAgent() and BlueAgent() offline-compatible so default Orchestrator and original tests work. Current team design: add LiveRedAgent(client, model) and LiveBlueAgent(client, model) in the respective owned modules, with the same generate_attack/analyze_event signatures. These are planned classes, not existing classes. Eman selects them in llm/setup.py after review. Explicit smoke scripts can instantiate them directly; no frontend required.

Zhaotong should retain MockRepository and add SQLiteRepository(db_path) with the same read contract. This is a planned class. Use injected dependencies to test integration without modifying composition files.

### Shared LLM helper

config.Settings.from_env() reads process environment; it does not load .env files. COMETCARE_MODE defaults to mock. Live requires GROQ_API_KEY. RED_MODEL/BLUE_MODEL/ENTERPRISE_MODEL have defaults in config.py.

llm.client.GroqClient(api_key).complete(model=..., messages=[...], tools=None, tool_choice='none') returns one assistant-message dict. Task-specific schema validation belongs in each agent. LLMError carries safe failure messages. The helper has bounded timeouts, 1,024 completion tokens and no automatic retries. Inject fake clients for ordinary tests. Do not change helper settings to mask malformed model output without Eman's review.

Local contributors use their own keys; Render's key serves integrated agents after Eman wires/merges/deploys them. Do not request keys in chat, read secret files, log credentials, or use VITE_ variables for secrets.


</details>

## Using Claude or Codex

Give your helper this file and your personal context file. Each personal file ends with a starter prompt. Ask it to inspect actual code, work only on the current stage, preserve teammate-owned files and contracts, explain changes, and run tests. Do not paste secrets or authorize the helper to implement everyone's tasks. No autonomous commits, pushes or deployments unless you request them.

Historical files in `docs/archive/` are not the active task list. This file and the four personal files are the current plan.
