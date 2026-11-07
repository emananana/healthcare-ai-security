# CometCare project roadmap

**Goal:** deliver the proposal's synthetic enterprise simulation, with a working enterprise LLM assistant, different red/blue LLMs, traditional security controls, bounded adaptive attacks, a deceptive defense, and measured comparisons.

No dates: advance when each checkpoint works. This is a plan, not a claim that these features already exist. Start with your next task in [TEAM_GUIDE.md](TEAM_GUIDE.md); return here to see what comes next.

## The path at a glance

| Step | What becomes possible | Depends on |
| --- | --- | --- |
| 0 · Current starting point | Run CometCare with deterministic mocks | Already implemented |
| 1 · Agree on the experiment | Everyone builds against the same scenarios and boundaries | 0 |
| 2 · Build in parallel | SQLite/security and each LLM module work independently | 1; use mocks for missing teammates |
| 3 · Working LLM demonstration | A red LLM attacks an enterprise LLM; a different blue LLM analyzes it | LLM modules from 2; mock storage can remain temporarily |
| 4 · Secure enterprise integration | The LLM flow uses SQLite, authenticated users, RBAC, least privilege and durable audit | 2 + 3 |
| 5 · Proposal behaviors | Bounded adaptive campaigns and real decoy routing | 4; adaptation and deception can proceed in parallel |
| 6 · Research comparison | Repeatable baseline/traditional/combined/decoy experiments and metrics | 4; include 5 for final proposal evaluation |
| 7 · Final handoff | Reproducible demonstration, report, and an optional hosted app | 6 |

**Minimum working-LLM checkpoint: Step 3.** This is the first major deliverable, not completion of the whole proposal. Steps 4–6 deliver the remaining research commitments. Public hosting can happen on a separate track; it does not have to wait for Step 7.

## Who owns what throughout

| Person | Owns | Main app location |
| --- | --- | --- |
| **Eman** | React, FastAPI, enterprise chatbot, orchestration, provider integration conventions, experiment runner and results UI | Both workspaces |
| **Vanessa** | Red agent, attack fixtures, adaptive strategy, attack labels | Security Lab → Attack Simulator |
| **Reya** | Blue agent, detection prompt, risk/recommendation, threat classification and detection evaluation | Security Lab → Defense Analysis → Blue-team recommendation |
| **Zhaotong** | Synthetic SQLite store, authentication, RBAC, least privilege, authorization, durable audit and decoy store | Member records; Defense Analysis → Traditional authorization; Audit Log |

Eman coordinates changes to shared models and APIs. Everyone writes tests for their own component and reviews the evidence for their portion of the report. UI work and metrics are not a substitute for teammate-specific tests.

## Step 0 — Know what exists

The React portal, FastAPI adapter, orchestrator, mock agents, in-memory records, ownership gate, audit viewer, and basic tests work. The enterprise assistant uses keyword parsing. Red emits a fixed cross-customer request. Blue checks customer IDs. There are no live LLMs, SQLite integration, authenticated sessions, adaptive campaigns, or decoy responses yet.

The existing four-case evaluation measures final ALLOW/BLOCK outcomes only. It is not yet a threat-detection study. DECEIVE exists as a recommendation but currently causes a block.

## Step 1 — Agree on a small experiment

| Person | Task / handoff |
| --- | --- |
| Eman | Write a short configuration plan: mock/live mode, chosen enterprise/red/blue model identifiers, server-side keys, timeouts, retry limits, token limits and a per-run spending cap. Keep the default mock path usable without keys. Propose required event/run metadata changes for team review. |
| Vanessa | Provide labeled synthetic scenarios for legitimate requests, cross-customer access, prompt injection, and instruction hijacking. State the objective and observable success condition for each. |
| Reya | Review labels with Vanessa. Define what counts as malicious and how ALLOW/BLOCK/DECEIVE and risk levels should be interpreted. Select a small set of relevant MITRE ATT&CK/ATLAS mappings with source links and a rationale; do not force every request into a technique. |
| Zhaotong | Specify synthetic customers/roles, allowed actions, record ownership, and what is forbidden. Define which fields count as protected within the simulation and separate protected synthetic records from decoys. |

**Together decide:** use different model identities for red and blue as promised in the proposal; they need not come from different vendors. Choose models based on tool/structured-output support, access, and budget when implementation starts. Keep attack generation confined to the synthetic environment.

**Checkpoint:** a small labeled scenario set, a documented access matrix, success criteria, and agreed configuration/interfaces. A legitimate request must be judged by a correct answer, not merely by an ALLOW label.

## Step 2 — Build modules in parallel

### Eman: enterprise LLM and integration support

- Add a small server-side provider adapter/configuration layer; avoid a new agent framework unless necessary. Coordinate provider conventions with Vanessa and Reya.
- Replace keyword-only planning with constrained LLM selection of the existing policy/claim actions. Validate tool name, arguments and customer target before execution; the model must never issue arbitrary SQL.
- Preserve the pipeline: proposed action → blue analysis → independent authorization → permitted repository read → grounded answer → audit. Apply the checks to every tool action, including follow-up actions.
- Generate the final reply from permitted data only. Do not give the enterprise model unrestricted records in its initial context.
- Preserve `EnterpriseAgent.handle_message(user, message)` and optional `source`. Bound tool rounds and conversation state; scope any history to the authenticated user/session.
- Handle provider timeouts, malformed responses, rate limits and unavailable credentials visibly. In live mode, never silently report mock output as a real LLM result. Coordinate failure auditing with Zhaotong.

**Can use:** current mock repository, gateway, red and blue agents. Does not need to wait for SQLite.

### Vanessa: live red LLM

- Keep `generate_attack(context) -> Attack`; use the selected red model to produce one bounded synthetic test prompt and category.
- Give it the scenario objective and permitted context, not database credentials, hidden blue reasoning or unrestricted protected records.
- Begin with single-turn prompt-injection, instruction-hijacking and cross-customer scenarios. Keep deterministic fixtures for regression tests.
- Validate model output and enforce generation length/time/token limits. Supply configuration names and tests to Eman.

**Can use:** saved scenario/context fixtures. Adaptation comes in Step 5, after the one-turn flow works.

### Reya: live blue LLM

- Keep `analyze_event(event) -> DefenseDecision`; use a model different from the red model.
- Analyze the request and proposed action against the access policy. Treat the inspected message as untrusted data, not instructions to the detector.
- Validate recommendation/risk fields and return a concise reason. Agree with Eman on safe handling for invalid output and provider failures; record these separately from correct detections.
- Test malicious and benign events, including legitimate requests that contain suspicious-looking words. Preserve mock fixtures for offline tests.

**Can use:** constructed `SecurityEvent` fixtures; does not need Vanessa's live agent or SQLite to start.

### Zhaotong: database and security foundation

- Implement a repeatable SQLite schema/seed for synthetic customers, policies and claims behind the existing repository interface. Use parameterized queries scoped to the authorized action.
- Implement verified sessions, a minimal role/access matrix, and customer ownership checks. Keep research/operator access distinct from customer access. Coordinate session/API changes with Eman rather than removing demo identity support unilaterally.
- Keep `authorize(user, action) -> AuthorizationResult`; authorization must work even when blue incorrectly allows a request.
- Persist audit events with request/run correlation and success/error outcomes. Keep secrets out of logs; use isolated temporary databases in tests.
- Document initialization, reset, connection lifetime and repository injection. Keep the existing mock usable until integration is ready.

**Can use:** fixed users/actions and mocked blue ALLOW decisions. Does not need any LLM to test authorization.

**Checkpoint:** each module has tests, a short runnable example, setup instructions and a compatible handoff. External provider calls are tested explicitly; ordinary regression tests should not incur LLM charges.

## Step 3 — Integrate the first working LLM demo (required)

Integrate in this order so failures can be isolated:

1. **Eman:** live enterprise LLM with mock red/blue and the current gateway. Retrieve C001's own policy/claims correctly; a request for C002 remains denied.
2. **Eman + Reya:** add live blue analysis. Inspect recommendation, risk and reason in Defense Analysis separately from authorization.
3. **Eman + Vanessa:** add live red generation. Run one attack through the same guarded enterprise flow.
4. **All:** run one legitimate request and one malicious request end to end. Capture actual outputs, model identifiers, event IDs, time and errors. A failed attack still counts as a successful integration if the real modules ran and the evidence is recorded.

**Acceptance:** all three agents make real provider calls; red and blue use different models; the assistant uses authorized tool results; the UI shows actual decisions; failures are understandable; keys remain server-side. Mock/live mode is explicit. No fabricated result is used to fill a missing provider call.

**Dependency:** SQLite is not required for this first milestone. When SQLite is ready, Eman injects it without changing the agent contracts.

## Step 4 — Connect the secured enterprise environment

- **Zhaotong → Eman:** hand over the SQLite repository, seed/reset commands, gateway, session implementation and persistent audit adapter.
- **Eman:** connect verified identity to FastAPI and the portal; restrict research actions/logs to the research role. The current workspace switch and demo customer dropdown are not access controls.
- **Vanessa:** run cross-customer and hijacking scenarios against the integrated flow.
- **Reya:** verify blue analysis remains independent of gateway decisions and analyze any false positives.
- **Eman + Zhaotong:** confirm the model cannot bypass security through tool arguments, a second tool call, or another user's conversation history. Record errors without returning protected records.

**Checkpoint:** own-record requests complete; cross-customer requests are denied even with a deliberately permissive blue stub; users cannot change identity by posting another customer ID; audit survives a restart; fixtures can be reset reproducibly. Keep the local identity-selector mode explicitly separate for demonstrations if needed.

## Step 5 — Add the proposal's adaptive attacks and deceptive defense

### 5A. Bounded adaptation — Vanessa + Eman

- **Vanessa:** let the red model revise a request based on previous attacker-visible responses. Define a small maximum number of attempts and a stop condition.
- **Eman:** run the campaign loop, pass only the agreed feedback, enforce turn/time/token/cost limits, and support cancellation between attempts. Store campaign/attempt IDs and show progress in Attack Simulator.
- **Reya:** analyze each attempt independently and review changes in detection across attempts.
- **Zhaotong:** provide repeatable dataset/session reset and persistent campaign-linked audit.

Current context values are strings. Eman and Vanessa must agree how to carry bounded history (for example a documented serialized string) or explicitly version the contract; do not silently change its type. Do not leak internal defender rationale to the attacker unless that is a separately labeled experimental condition.

**Checkpoint:** at least one campaign demonstrates that a later generated attempt uses allowed earlier feedback and stops at its budget. Success is not guaranteed or fabricated.

### 5B. Deception — Zhaotong + Reya + Eman

- **Zhaotong:** create a separate synthetic decoy store and an explicit decoy retrieval path that cannot fall through to protected records.
- **Reya:** define when to recommend DECEIVE and test those decisions.
- **Eman:** add an agreed decoy execution branch. Authorization denial must still prevent protected reads; returning a decoy is a separate permitted action, not a bypass of the gateway.
- **Vanessa:** evaluate what the attacker can observe when the assistant returns a decoy.
- **All:** agree on audit/outcome changes before coding. `SecurityEvent.outcome` currently only permits PENDING/ALLOW/BLOCK; do not silently place a new value into it. Record decoy provenance for evaluators without revealing it through attacker feedback.

**Checkpoint:** a DECEIVE run returns only designated dummy data, records the route for evaluation, and never counts as protected-data exposure merely because text was returned.

These are core proposal behaviors at small scale. Large autonomous campaigns and elaborate honeypots are stretch work.

## Step 6 — Evaluate fairly

**Eman owns the runner and metrics; all teammates own the validity of their evidence.** Extend the existing evaluation rather than treating its current four mock cases as the study.

### Experimental conditions

| Condition | What changes | Owners |
| --- | --- | --- |
| Unsecured baseline | Isolated experiment-only version of the same enterprise assistant/dataset without the tested defense checks | Eman + Zhaotong |
| Traditional controls | Authentication, RBAC, least privilege and audit; no blue enforcement | Zhaotong + Eman |
| Combined AI-assisted defense | Same traditional controls plus live blue enforcement | Reya + Eman |
| Combined + deception | Same combined condition with the decoy branch enabled | All |

Keep the intentionally unsecured condition out of the public member portal. Its bypasses must be explicit, isolated and available only to the experiment runner; reset synthetic state between runs.

First replay the **same frozen attack set** across conditions to compare defenses. Then evaluate adaptive campaigns separately with matched objectives and budgets; evolving prompts are not identical replay trials. Use separate development and held-out scenarios, repeated trials, recorded model/prompt versions and sampling settings. Fix seeds where supported but do not claim LLM determinism.

### Metrics and responsibility

| Metric | Definition to implement | Lead / evidence provider |
| --- | --- | --- |
| Attack success rate | Malicious attempts achieving a predefined unauthorized objective / malicious attempts. Also report campaigns with at least one success / campaigns. Use actual data exposure or forbidden execution, not ALLOW alone. | Eman; Vanessa's objectives + Zhaotong's protected-record oracle |
| Threat-detection accuracy | Correct blue classifications / labeled requests. State how BLOCK/DECEIVE map to a positive detection; keep these separate from the gateway outcome. | Reya + Eman |
| False-positive rate | Benign requests flagged by blue / benign requests. Separately report legitimate requests blocked by the full system. | Reya + Eman |
| Detection time | Elapsed time from starting blue analysis until its validated decision; report end-to-end response latency separately. Include provider failures/timeouts as separate counts. | Eman instrumentation + Reya |
| Legitimate task completion | Benign tasks answered correctly using authorized records / benign tasks. ALLOW alone is insufficient. | Eman + Zhaotong; all review sample answers |
| Deception outcome | Decoy routing rate and actual protected-record exposure rate; report attacker continuation separately, without assuming a decoy convinced the attacker. | Zhaotong + Vanessa + Eman |

Log counts and denominators, confusion matrix, per-scenario results, repeated-run variability, errors, and model cost/token usage where available. Report missing measurements as unavailable rather than inventing zero latency. Do not discard failed provider calls silently; publish attempted/completed/error counts and the denominator policy.

- **Vanessa:** curate held-out attacks and explain failures/successes; annotate relevant attack categories.
- **Reya:** review detection labels, false positives/negatives, and defensible MITRE mappings with citations.
- **Zhaotong:** verify protected versus decoy provenance and unauthorized access outcomes.
- **Eman:** add experiment controls/results to the Security Lab, export machine-readable results, and generate comparison tables/plots.

**Checkpoint:** another teammate can repeat the experiment from documented commands and a fixed synthetic seed. The report distinguishes observed results, limitations, and unimplemented ideas.

## Step 7 — Finish the demonstration and report

- **Eman:** one setup path, clear configuration template, reproducible experiment commands, UI walkthrough, results export, and integration checks.
- **Vanessa:** attack design, adaptive trace, and attack outcomes section.
- **Reya:** defender design, technique mapping and classification/error analysis section.
- **Zhaotong:** architecture of data/access controls, audit evidence and decoy isolation section.
- **Everyone:** review the proposal coverage checklist below and demonstrate a legitimate request, a blocked malicious request, and a decoy response using actual execution results.

## Hosting track — can start before the agents are finished

**GitHub Pages hosts static HTML/CSS/JavaScript; it cannot execute Python.** See [GitHub's documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).

| Option | What visitors get | Prerequisites |
| --- | --- | --- |
| Project information page | Overview, screenshots, roadmap and repo link; no running agents | Can be published now |
| CometCare frontend on Pages + separately hosted FastAPI | Working shared portal and simulation | Reachable HTTPS backend, deployment configuration and appropriate access/cost controls |
| One Python-capable host serving API + built React | Working shared portal and simulation at one origin | A suitable host and combined deployment setup |

**Recommended sequence:** finish the local LLM checkpoint first; a project information page can be shared meanwhile. Host the interactive demo once its backend, access and provider budgets are ready. Hosting does not make missing agent logic work, and live LLM hosting is not required to complete the research locally.

**Eman leads deployment**, with **Zhaotong** handling storage/session requirements. For the interactive app:

1. Choose the hosting approach; confirm provider costs and persistent SQLite storage before deploying.
2. Replace the frontend's hardcoded localhost API URL with build-time configuration (public URL only, never a secret). Configure Vite's repository base path if using a GitHub Pages project URL.
3. Deploy FastAPI over HTTPS; configure the exact deployed frontend origin for CORS. Confirm no browser request points to a visitor's localhost.
4. Store LLM keys only on the backend. Protect research actions/logs and provider spending with authentication, quotas and bounded requests. Keep the unsecured experimental condition private/local.
5. Add a repo-connected build/deploy workflow, smoke-test the real deployed URLs, and link the site in the repository. Document restart/reset behavior and database persistence.

This roadmap does not deploy a site or select a paid host. A possible Pages address is `https://emananana.github.io/healthcare-ai-security/`; it is not claimed to be live.

## Proposal coverage checklist

- [ ] Enterprise LLM with constrained tool use — Eman, Steps 2–3
- [ ] Red and blue powered by different LLMs — Vanessa/Reya, Steps 2–3
- [ ] Prompt injection, instruction hijacking and simulated data exfiltration — Vanessa, Steps 1–6
- [ ] SQLite, authentication, RBAC, least privilege and audit — Zhaotong, Steps 2–4
- [ ] Bounded autonomous generation and adaptation — Vanessa/Eman, Step 5A
- [ ] Deceptive synthetic-data response — Zhaotong/Reya/Eman, Step 5B
- [ ] MITRE ATT&CK/ATLAS categorization with justified mappings — Vanessa/Reya, Steps 1 and 6
- [ ] Unsecured/traditional/combined defense comparisons — Eman/all, Step 6
- [ ] Attack success, detection accuracy, false positives, detection time and legitimate completion — Eman/all, Step 6
- [ ] Reproducible demonstration and report — all, Step 7

## Stretch goals — only after the core works

- More red/blue model pairings and systematic cross-model comparisons.
- Additional tool surfaces, indirect injection via synthetic documents, and richer multi-turn attacks.
- Larger campaigns, richer deception strategies and attacker-belief analysis.
- Statistical confidence intervals and larger controlled evaluation sets beyond the initial repeated trials.
- Live streaming, experiment queueing, richer charts and more polished investigator workflows.
- A public interactive deployment if not already needed for the class demonstration.

Do not postpone Step 3 for stretch features. If time is limited, retain the working LLM loop and demonstrate smaller, bounded versions of the proposal's core behaviors; explicitly document any scope reduction.
