# Eman — integration owner

## What is already done

- React member portal and Security Lab, FastAPI adapter and stable contracts.
- Shared Groq helper/configuration and bounded enterprise tool execution.
- Live enterprise chatbot tested by you; Render shared app is working.
- Team access gate, request throttle, Docker setup and offline integration tests.

You do not need to write Vanessa's, Reya's or Zhaotong's implementations. Your next job is to make their independent pieces easy to connect.

## Do now

1. Share the README, each person's guide and shared app URL: https://healthcare-ai-security.onrender.com/. Share the team password privately; never share the server Groq key.
2. Have each person create their branch and run baseline tests before editing. They use their own local keys for live checks.
3. Confirm the handoff shapes in PROJECT_CONTEXT.md: keep offline defaults; add LiveRedAgent(client, model), LiveBlueAgent(client, model), and SQLiteRepository(db_path). These classes are proposed interfaces for their new work, not already implemented classes.
4. Before the next merge, capture a quick baseline: C001's own policy returns a record; C001 asking for C002 claims is denied; Attack Simulator creates an audit event. This is a manual smoke check, not a formal evaluation result.

No major new feature is needed before teammates start. You can prepare experiment scenarios later while their modules are underway.

## When Vanessa or Reya opens a PR

1. Review the diff for owned files and compatible signatures. Run the full offline tests on their branch. Ask for a sample output and explicit manual smoke script. Don't accept keys in commits or test fixtures.
2. Test one real call locally using your own environment key. Check invalid output, rate limits and provider refusal behavior separately from successful detections.
3. In `llm/setup.py`, select the new live class only in live mode and inject the existing shared GroqClient plus `settings.red_model` or `settings.blue_model`. Keep mock mode usable without keys. Each module can be integrated independently; the other can remain mock.
4. In `main.py`, update `/api/status` to reflect the actual selected agents. It currently reports red/blue as mock. Do not mark an unconnected class live merely because it exists.
5. Verify errors across the pipeline. `main.py` already handles LLMError as 502, but red generation and blue analysis do not currently have the same incomplete-event audit handling as enterprise planning. Add compatible handling/tests where needed; never convert a provider failure into ALLOW or claim it was a successful BLOCK. If no action/event exists yet, report that limitation instead of inventing an attack result.
6. Test through the local app: generated attack → blue recommendation → independent authorization → final result → audit. Check both same-customer and cross-customer requests.
7. Run `python -m unittest discover -s tests -v` and `npm run build --prefix frontend`.
8. Merge the reviewed component and wiring together into `main`. Wait for a successful Render deployment, then repeat the shared-app smoke check and confirm the updated mode labels.

**You merge their PRs.** Their branch pushes are not automatically deployed by the current main-branch service. Resolve conflicts on the integration branch without overwriting teammate work. No need to collect teammates' API keys; Render uses its existing server key for all selected models.

## When Zhaotong opens a PR

1. Run seed and repository/security tests in a temporary database. Verify repeat seeding and authorization independent of blue output.
2. Add one database-path setting and instantiate her SQLite repository in `llm/setup.py`; keep mock mode's fixtures available. Follow her seed/init instructions rather than guessing schema setup.
3. Keep startup/schema migration separate from destructive resets. Do not overwrite user-created experiment data during every deploy.
4. Test own-record reads, missing records, cross-customer denial and restart behavior locally. Wire her persistent audit adapter in a later PR when ready.
5. **Before claiming hosted persistence:** choose persistent storage. The current free Render disk is ephemeral. A reset/reseed shared demo can be acceptable if clearly labeled; durable experiment evidence must be exported/stored elsewhere or use an approved persistent hosting option. Do not change to a paid plan without approval.
6. Individual authentication/roles require API identity changes with Zhaotong. The current shared password and customer dropdown do not implement that proposal requirement.

## After all three modules are integrated

Own the orchestration/evaluation work: bounded red feedback loop, explicit decoy route agreed with Reya/Zhaotong, fixed labeled scenarios and held-out runs, and comparisons of unsecured/traditional/combined/deception conditions. Keep intentionally unsecured execution out of the public member portal.

Measure actual unauthorized exposure, blue classification accuracy/false positives, detection time and correct legitimate answers—not just final ALLOW/BLOCK. Ask Vanessa for attack objectives, Reya for detection labels and Zhaotong for expected record/access outcomes. Record model/configuration and provider failures.

Hosting maintenance is in the expandable reference below. Older plans in docs/archive are historical, not prerequisites.

## Ordered final goals and stretch goals

1. Finish the independent-module handoffs and integration checks above. Keep visible mock/live status truthful.
2. Connect SQLite, verified sessions/roles, and persistent audit with Zhaotong. Resolve hosted storage explicitly before claiming durability.
3. Add the bounded attack runner with Vanessa: limited turns/time/tokens, attacker-visible feedback only, cancellation between attempts, and campaign IDs. Agree on shared schema additions first.
4. Connect Reya's DECEIVE recommendation to Zhaotong's isolated decoy path; preserve denied access to protected records and record provenance for evaluation. Current outcome enums do not include a deception outcome—coordinate changes rather than inserting unsupported values.
5. Build reproducible comparisons: fixed development/held-out scenarios; unsecured (isolated runner only), traditional, combined AI-assisted and deception conditions; repeated trials; actual exposure, blue accuracy/false positives, detection time, legitimate completion and provider errors. Compare adaptive runs separately at matched budgets.
6. Export results and assemble the final walkthrough/report with each teammate's evidence. Check the shared demo after every successful deployment.

**Stretch goals, in order:** clearer result charts → live campaign progress → additional model-pair comparisons → larger experiments and stronger statistical analysis. Streaming and UI polish should not delay core research functionality.

## Paste this into Claude or Codex when integrating a PR

```text
I am Eman, the CometCare integration owner. Read PROJECT_CONTEXT.md, README.md
and context/EMAN.md. Inspect the actual PR and existing implementation first.
Integrate only the teammate module I identify, preserving its public contract
and all other teammate-owned implementations. Keep offline mock mode.
Wire compatible live implementations in llm/setup.py with the shared Groq
client/config. Make /api/status reflect the actual selected modes. Check
provider failures and incomplete-event auditing without fabricating outcomes.
Use tests with fake clients/temp databases; run the existing suite and frontend
build. Do not call real models without asking, expose keys, bypass authorization,
add unrelated features, change hosting plans, commit, push, merge or deploy
without my instruction. Explain exactly what changed and how to smoke-test
locally and after deployment. If a teammate contract is incompatible, explain
it and propose a small coordinated change rather than rewriting their module.
```

<details>
<summary><strong>Hosting maintenance reference (already deployed)</strong></summary>

# Hosting reference — Eman only

The shared app is https://healthcare-ai-security.onrender.com/. It is already deployed; these are maintenance/reference instructions, not teammate setup tasks.

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


</details>
