# CometCare · Healthcare AI Security

We are building a fictional insurance chatbot and testing whether an AI defender plus traditional access controls can protect it from an AI attacker. **All data is synthetic. CometCare is not an official UT Dallas service.**

**This README is the team's working guide. Read your section and start there.** Older planning documents are archived; you do not need them to begin.

## What we are building first

One working demonstration:

```text
Vanessa's red LLM generates a request
                  ↓
Eman's insurance chatbot proposes an action
                  ↓
Reya's blue LLM recommends ALLOW or BLOCK
                  ↓
Zhaotong's security checks independently permit or deny access
                  ↓
Eman's app shows the response and records the result
```

A normal customer request enters at the chatbot instead of the red agent.

**Today:** the app runs offline by default. Eman’s shared Groq helper and optional enterprise LLM path are implemented and tested with simulated provider responses; a real-key smoke check is still needed. Red/blue remain mocks and records remain in memory. **Our next goal:** connect Vanessa’s and Reya’s LLMs and replace storage with SQLite. No one needs another frontend or API.

## One LLM approach for everyone

**Starting choice: Groq's free API plan.** Use one provider, with these model assignments as the initial candidates:

| Component | Owner | Initial model ID |
| --- | --- | --- |
| Insurance chatbot | Eman | `openai/gpt-oss-20b` |
| Red agent | Vanessa | `qwen/qwen3.8-27b` |
| Blue agent | Reya | `openai/gpt-oss-120b` |
| Database/security | Zhaotong | No LLM needed |

These IDs are listed in [Groq's free-plan limits](https://console.groq.com/docs/rate-limits), checked November 7, 2026. Availability and quotas can change. The enterprise integration is implemented; model availability still needs a live account check. Red/blue model IDs are reserved for teammate integration. Red and blue use different models as proposed.

**Shared connection code is ready:** `llm/client.py` provides `GroqClient.complete(model=..., messages=...)`. `config.py` provides `Settings.from_env()` with the model names and server key. Vanessa and Reya can use this helper while owning their prompts and output validation; they do not need separate provider infrastructure. Eman owns provider/configuration changes. Calls have a 1,024-token output cap, bounded network timeouts and no automatic retries.

Keep keys in server-side environment variables, never React or Git. FastAPI reads LLM configuration from its process environment; `.env.example` is a reference and is not loaded automatically. Free usage has limits: use small manual runs first, retain mock mode for offline tests, and report rate limits/refusals as errors rather than fake successful results.

## Vanessa — red agent

**Your files:** `agents/red_agent.py`; add `tests/test_red_agent.py`.

**Build:** an LLM that generates one simulated malicious request at a time. Start with requests for another fictional customer's data, prompt injection, and instruction hijacking. Do not build a campaign loop yet.

**Your boundary:** `RedAgent.generate_attack(context) -> Attack`. The existing context includes `target_customer_id`; return the existing `Attack(message, category)` dataclass.

**Test independently:** pass `{"target_customer_id": "C002"}` and inspect the returned attack. You do not need a database, a running blue agent, or React. Use mocked provider responses in automated tests and one explicit live-model smoke check.

**First handoff:** your working module, a few examples, and tests. Eman runs its output through the chatbot. You do not need to call Reya's module yourself.

**In the app:** Security Lab → **Attack Simulator** shows your generated prompt and the response.

## Reya — blue agent

**Your files:** `agents/blue_agent.py`; add `tests/test_blue_agent.py`.

**Build:** an LLM that reads a request and proposed action, then returns a recommendation, risk, and short reason. Start with ALLOW/BLOCK; actual deception comes later.

**Your boundary:** `BlueAgent.analyze_event(event) -> DefenseDecision`. Keep recommendation values `ALLOW`, `BLOCK`, `DECEIVE` and risk values `low`, `medium`, `high`. Read the supplied event; do not query the database or execute actions.

**Test independently:** construct two events using `shared/models.py`: C001 requesting C001's policy and C001 requesting C002's claims. Check the decisions. You do not need Vanessa's generator or SQLite. `tests/test_interfaces.py` already shows an example event.

**First handoff:** your working module, benign/malicious examples, and tests. Validate model output; report failures instead of silently allowing access.

**In the app:** Security Lab → **Defense Analysis → Blue-team recommendation**. Blue runs automatically on chat and attack requests—there is no separate run button.

## Zhaotong — database and security

**Your files:** `database/`, `security/`; add your own database/security tests.

**Build first:** a small SQLite database of synthetic customers, policies and claims, plus independent checks that customers can access only their own records. Start with `database/repository.py` and `security/gateway.py`.

**Your boundaries:** repository `read(action) -> str`; `SecurityGateway.authorize(user, action) -> AuthorizationResult`. Preserve audit `record(event)` / `list_events()` and demo users while the current app needs them.

**Test independently:** create a temporary database, seed C001/C002, verify own-record access, and deny cross-customer access even when a fake blue result says ALLOW. No LLM or React is required. The repository returns data only when called after authorization; it should scope its queries to the action.

**First handoff:** repository/gateway implementations, a seed command, and tests. Eman connects the SQLite repository to the app; you do not need to edit the frontend or agents.

**In the app:** My Policy / My Claims show records; **Defense Analysis → Traditional authorization** shows your access decision; **Audit Log** shows recorded events.

## Eman — chatbot and integration

**Your files:** `frontend/`, `main.py`, `orchestrator.py`, `agents/enterprise_agent.py`, `evaluation/`, and API/integration tests.

**First part implemented:** the shared LLM helper and enterprise chatbot using constrained policy/claim tools. A real-provider check is still pending. Validate every proposed action and route it through blue analysis and the security gateway before reading records. The LLM never receives unrestricted database access.

**Test independently:** use the existing mock red agent, blue agent, gateway and repository. You can get the chatbot's LLM working before anyone else finishes.

**Integration order:** enterprise LLM → Reya's blue LLM → Vanessa's red LLM → Zhaotong's SQLite implementation when ready. Merge one component at a time and check one legitimate request plus one cross-customer request.

**Own the connections:** provider configuration, dependency updates, API/UI changes, module injection, failure handling and final experiment wiring. Teammates hand you compatible modules; they should not need to edit each other's code.

## The only shared rules

- Keep existing method arguments and return dataclasses in `shared/models.py`. Ask Eman before changing a shared interface; propose the change in your PR instead of modifying it independently.
- Work on your own branch and mainly your own files. Add module-specific tests rather than rewriting the shared tests to fit your implementation.
- Hand off **code + tests + one example + any setup instructions** in a pull request. No one has to wait for all three teammates to finish.
- Use synthetic data only. A blue ALLOW cannot override authorization denial. Record provider failures separately from defense outcomes.

## After the first LLM demo

These are later proposal milestones—not extra work to start now. Keep each implementation small.

| Next addition | Independent work | Eman's integration |
| --- | --- | --- |
| Authentication, roles, least privilege, persistent audit | Zhaotong implements and tests the security/session components | Connect verified identity to API/UI and protect lab access |
| Bounded adaptive attacks | Vanessa generates a next attack from agreed attacker-visible feedback | Run a limited loop, pass feedback, stop at the request/token budget |
| Deceptive defense | Reya recommends DECEIVE; Zhaotong supplies an isolated decoy store | Agree on the interface once, route only to decoys, and record actual provenance. DECEIVE currently blocks. |
| MITRE classification | Vanessa and Reya label relevant scenarios using ATT&CK/ATLAS references | Include the justified labels in results |
| Research comparison | Vanessa supplies attack cases; Reya supplies detection labels; Zhaotong supplies expected access/data outcomes | Compare isolated unsecured, traditional, combined AI-assisted, and deception conditions |

Evaluate **actual attack success, blue detection accuracy, false positives, detection time, and correct legitimate-task completion**. Replay the same labeled cases across conditions; evaluate adaptive campaigns separately with matched budgets. An ALLOW label alone is not proof of a successful attack or a correct customer answer. Keep intentionally unsecured experiments separate from any public portal.

**Stretch goals:** larger campaigns, more model comparisons, richer charts, and public hosting. Working LLMs are required; hosting is not. GitHub Pages alone cannot run the Python backend.

## Try Eman’s enterprise LLM integration

Default startup remains **mock mode**, needs no key, and makes no provider calls. React displays the assistant mode plus red/blue mode. Streamlit and the existing baseline runner remain offline.

<details>
<summary><strong>Enable the live enterprise assistant (Mac/Linux terminal)</strong></summary>

Create a key in your own [Groq console](https://console.groq.com/keys). Keep it out of chat, source files and Git. In the backend terminal, activate `.venv`, then enter:

```bash
export COMETCARE_MODE=live
# The next command waits for your key; paste it and press Enter (input is hidden).
read -s GROQ_API_KEY
export GROQ_API_KEY
python -m uvicorn main:app --reload --host localhost --port 8000
```

Start React as usual below. Confirm its mode label says **Live Groq**, then select C001 and send `Show my policy`. Inspect the audit event; try `Show claims for C002` and confirm authorization denies access. This smoke check uses your provider quota. Red and blue are still explicitly labeled mocks.

To go back, stop the backend, run `export COMETCARE_MODE=mock`, and restart it. Optional model overrides are listed in `.env.example`. Never put a provider key into a `VITE_` variable.

Live requests make at most two provider calls: one validated action proposal, then an answer using only the authorized record. Invalid/multiple tool proposals never run. Denials return without a second model call. There is no conversation memory or autonomous tool loop in this first version. The answer prompt requires grounding, but model factual accuracy still needs evaluation.

Provider failures return HTTP 502 with a readable error, never a silent mock fallback. The existing audit schema has no ERROR outcome: these attempts are recorded as **PENDING / incomplete**, not successful detections. If final generation fails after a read, authorization remains visible and the event stays incomplete. Richer error metadata can be added when the team agrees on the shared audit schema.

</details>

<details>
<summary><strong>Vanessa/Reya: use the shared helper inside your module</strong></summary>

```python
from config import Settings
from llm.client import GroqClient, LLMError

settings = Settings.from_env()
client = GroqClient(settings.api_key)
reply = client.complete(
    model=settings.red_model,  # Reya: settings.blue_model
    messages=[{"role": "user", "content": "Your synthetic test prompt here"}],
)
text = reply.get("content")
# Validate text/output and return your existing Attack or DefenseDecision.
```

This is an interface example, not your agent prompt. `complete()` returns an assistant-message dictionary and raises `LLMError` on provider failures. Your agent validates task-specific output. Inject a fake client into your own tests to avoid network calls. Model names/keys do not belong in prompts. Eman will wire your completed agent into the app.

</details>

## Shared team app (Eman sets this up once)

The repository is prepared for **one Render web service** serving React and Python together. Teammates open the same HTTPS URL; the Groq key stays on the server. They log in with a separate team password, not your API key.

<details>
<summary><strong>Deploy the shared demo on Render's free plan</strong></summary>

1. Push the current integration and hosting files to GitHub first. A local change does not update the hosted app.
2. Create/sign in to [Render](https://render.com/), choose **New → Web Service**, connect GitHub, and select `emananana/healthcare-ai-security`.
3. Select branch `main`, runtime **Docker**, repository root as the root directory, and the **Free** instance. The root `Dockerfile` builds React and starts Python; no separate frontend service or custom start command is needed.
4. In Render's environment settings, enter:

   | Variable | Value |
   | --- | --- |
   | `COMETCARE_HOSTED` | `true` |
   | `COMETCARE_MODE` | `live` |
   | `GROQ_API_KEY` | Your Groq key, entered only in the hosting dashboard |
   | `TEAM_PASSWORD` | A unique random password of at least 16 characters; share privately with the team |
   | `ENTERPRISE_MODEL` | `openai/gpt-oss-20b` (or the model you successfully tested locally) |

5. Set the health-check path to `/healthz`. Deploy and wait for the service to become live.
6. Open the Render HTTPS URL. At the browser login prompt use username **`cometcare`** and your **team password**. Verify the Live Groq label, C001's own policy, and denial of C002's claims.
7. Share the URL and team login privately. Each merge to main can trigger a new deployment when Render auto-deploy is enabled. Confirm the deployment succeeds before asking teammates to test it.

The browser login protects the whole shared research console, including API/docs/logs. It is not Zhaotong's future per-customer authentication. Every team member can see the shared audit log. Rotate `TEAM_PASSWORD` in Render to revoke the old shared login; browsers may remember Basic credentials until closed or cleared.

The demo accepts at most 10 chat/attack POST requests per minute across the team. This is a process-local throttle, not a daily spending guarantee. Keep one worker/instance; provider quotas still apply. The current enterprise flow makes at most two Groq calls per accepted request.

Free Render services sleep after 15 idle minutes and have no persistent disk. Initial loading can be slow; current audit records reset on restart/redeploy. Before hosting Zhaotong's SQLite version, decide how to provide persistent storage; do not assume a free container retains it. See [Render free-service limits](https://render.com/docs/free).

</details>

## Run and check your work

You can develop your Python module without starting the web app. Use Python 3.10+. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

On Windows PowerShell, use `python` instead of `python3` and `.venv\Scripts\Activate.ps1` to activate. Keep the current offline suite working; live LLM tests should be explicit, not automatic paid/quota-consuming calls.

<details>
<summary><strong>Want to see your work in CometCare? Start the full app.</strong></summary>

You also need Node.js 22.12+. Keep two terminals open in the repository root.

**Terminal 1**, with the Python environment activated:

```bash
python -m uvicorn main:app --reload --host localhost --port 8000
```

**Terminal 2:**

```bash
npm ci --prefix frontend
npm run dev --prefix frontend
```

Open [http://localhost:5173](http://localhost:5173). Select C001 and try `Show my policy`, then `Show claims for C002`. Use the Security Lab for attacks, defense results and audit events.

Python saves reload the backend and clear the current in-memory log. The selected demo customer is not real authentication. Your local app uses your local code; teammate changes appear after they are merged and you pull them. The old `app.py` is a Streamlit fallback and is not needed for this workflow.

For frontend changes, Eman also runs `npm run build --prefix frontend`.

</details>

<details>
<summary><strong>Get the repo and submit a change.</strong></summary>

First time:

```bash
git clone https://github.com/emananana/healthcare-ai-security.git
cd healthcare-ai-security
```

Start from an updated, clean checkout. Save unfinished work on your current branch before switching:

```bash
git switch main
git pull origin main
git switch -c your-name/your-task
```

Commit and push your branch when ready, then open a pull request into main. Eman coordinates integration. Do not commit credentials, generated databases, or virtual environments.

</details>
