# CometCare · Healthcare AI Security

Our university project uses a **fictional insurance portal** to study simulated attacks and defenses. All records are synthetic. The app works today with simple mock agents; no API keys are needed. 

**New to the repo? Run the app below, then read only your section in [TEAM_GUIDE.md](TEAM_GUIDE.md).**

## 1. Get the project

Clone the repository, then open its folder in VS Code:

```bash
git clone https://github.com/emananana/healthcare-ai-security.git
cd healthcare-ai-security
```

Already have a clone? Update your clean checkout with `git switch main` and `git pull origin main`. Save any unfinished work on your own branch first.

## 2. Run the app

You need **Python 3.10+** and **Node.js 22.12+**. Open two VS Code terminals in the project folder. Keep both running.

**Terminal 1 — Python backend**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --host localhost --port 8000
```

On Windows PowerShell, use `python` instead of `python3` and `.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`.

**Terminal 2 — frontend**

```bash
npm ci --prefix frontend
npm run dev --prefix frontend
```

Open **[http://localhost:5173](http://localhost:5173)**. Next time, you can skip creating the virtual environment and installing dependencies unless requirements changed. 

## 3. Take a two-minute tour

| In the app | Try this |
| --- | --- |
| **Member Portal → AI Assistant** | Select C001 and send `Show my policy`. You should get that member's synthetic policy. |
| **Member Portal → AI Assistant** | Send `Show claims for C002`. The request should be blocked. |
| **Security Lab → Attack Simulator** | Click **Run simulated attack** to execute the red agent. |
| **Security Lab → Defense Analysis** | See the blue recommendation, separate authorization decision, and final outcome. |
| **Security Lab → Audit Log** | Inspect the requests and their recorded decisions. |

**Blue runs automatically** on chat requests, policy/claim retrievals, and attacks. There is no separate blue-team run button.

## 4. Find your work

| Person | Start here | See results here |
| --- | --- | --- |
| Vanessa — red team | [agents/red_agent.py](agents/red_agent.py) | Attack Simulator |
| Reya — blue team | [agents/blue_agent.py](agents/blue_agent.py) | Defense Analysis |
| Zhaotong — database/security | [database/repository.py](database/repository.py), [security/gateway.py](security/gateway.py) | Member records, authorization decisions, Audit Log |
| Integration owner — frontend/chatbot/API | `frontend/`, `main.py`, `orchestrator.py`, `agents/enterprise_agent.py` | Both workspaces |

Task and handoff instructions are in **[TEAM_GUIDE.md](TEAM_GUIDE.md)**. Detailed interfaces are in [docs/INTEGRATION.md](docs/INTEGRATION.md)

Before handing off code, activate your virtual environment and run:

```bash
python -m unittest discover -s tests -v
```
