# OnTrack AI: Student Retention & Risk Detection Framework

OnTrack AI is an agentic framework designed for the **Universidad Tecnológica del Sur de Sonora** to proactively detect early, latent signs of student risk and academic simulation (such as sudden drop-offs in LMS activity or plagiarized assignments) and apply the IDSRAL protocol.

---

## 🏗️ Project Architecture & Structure

```
ontrack-ai/
├── .agents/                 # Installed local development skills
├── app/                     # Core ADK Agent implementation
│   ├── agent.py             # Main ADK agent definitions & callbacks
│   ├── fast_api_app.py      # FastAPI gateway for ADK integration
│   └── app_utils/           # Core telemetry & session helpers
├── skills/                  # Custom agent skills
│   └── idsral-psychometrics/# Protocol definitions for MSLQ & Schaufeli index
├── src/                     # Multi-Agent Orchestration & Web Dashboards
│   ├── app_tutor.py         # Faculty/Tutor UI Dashboard (FastAPI app)
│   ├── main.py              # Local CLI execution flow pipeline
│   ├── agents/              # Pipeline sub-agents
│   │   ├── orchestrator.py  # Central risk evaluator & injection block
│   │   ├── telemetry_fleet.py # Telemetry collection coordinator
│   │   └── intervention_desk.py # Tutor action plan text generator
│   └── tools/               # Security & API integrations
│       ├── mcp_client.py    # Moodle/LMS telemetry mockup fetcher
│       └── privacy_gate.py  # SHA256 PII sanitization gate
├── tests/                   # Empirical Evaluation & Test Suite
│   ├── mock_cohort_profiles.json # Seeding data for simulations
│   ├── test_injection_guard.py  # Tests verifying prompt injection security
│   └── integration/         # Multiagent and server E2E test flows
├── Dockerfile               # Multipurpose container blueprint
├── GEMINI.md                # AI-assisted development instructions
└── pyproject.toml           # Project dependencies managed via uv
```

---

## 🛡️ Key Features & Security Controls

### 1. Zero-Trust PII Sanitization
Incoming student identifiers (emails, names, IDs) are programmatically hashed into cryptographic tokens (`student_sha256_xxx`) via the [privacy_gate.py](file:///C:/Users/tportela/ontrack-ai/src/tools/privacy_gate.py) before reaching any Large Language Model.

### 2. Prompt Injection Defense
Adversarial instructions inside text feeds or raw logs (e.g. attempting to override risk assessments to `LOW`) are blocked using context hygiene inside [orchestrator.py](file:///C:/Users/tportela/ontrack-ai/src/agents/orchestrator.py). The system isolates execution parameters and strictly enforces structured logic.

### 3. Stateful Crisis Circuit Breaker
If text logs indicate severe emotional distress, self-harm, or domestic violence, a dedicated circuit breaker inside [app_tutor.py](file:///C:/Users/tportela/ontrack-ai/src/app_tutor.py) and [agent.py](file:///C:/Users/tportela/ontrack-ai/app/agent.py) triggers:
- Normal diagnostic flows are halted immediately.
- The case is bypassed and routed to the **"Unidad de Apoyo al Estudiante"** for emergency human intervention.
- The Faculty/Tutor UI transitions into a striking red-alert alarm layout.

---

## 🚀 Running locally

### Prerequisites
Ensure you have `uv` and `google-agents-cli` installed:
```bash
# Install uv tool
uv tool install google-agents-cli
```

### Install Dependencies
```bash
# Sync virtual environment and dependencies
agents-cli install
```

### 1. Run the Agent Playground
Starts the ADK interactive console to chat with the early detection agent:
```bash
agents-cli playground
# Available at http://127.0.0.1:8080/dev-ui/?app=app
```

### 2. Run the Faculty / Tutor UI Dashboard
Starts the interactive simulation dashboard featuring HSL dark-mode styling, mock profile loading, and crisis red-alert triggers:
```bash
uv run python src/app_tutor.py
# Available at http://127.0.0.1:8050/
```

### 3. Run Pre-Deployment Tests
```bash
uv run pytest tests/unit tests/integration
```

---

## ☁️ Deploying to Google Cloud Run

Ensure you have configured `gcloud` with the correct project:
```bash
gcloud config set project ontrack-ai-501705
```

### Deploying the ADK Backend Agent
```bash
agents-cli deploy --deployment-target cloud_run --no-confirm-project --project ontrack-ai-501705
```

### Deploying the Faculty/Tutor Dashboard UI
```bash
gcloud run deploy ontrack-tutor-ui \
  --project ontrack-ai-501705 \
  --region us-east1 \
  --source . \
  --command="uv,run,python,src/app_tutor.py" \
  --port=8050 \
  --allow-unauthenticated
```
