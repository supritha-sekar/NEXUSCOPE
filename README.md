# NEXUSCOPE — AI Incident Intelligence & Response Copilot

NEXUSCOPE is a hackathon-ready GenAI platform for turning messy incident reports into structured intelligence, prioritised actions, resource plans, and auditable decisions.

## Why it matters
Emergency/public-service teams often receive fragmented reports and have to manually decide:
- What happened?
- How severe is it?
- What needs attention first?
- Which resources are needed?
- What information is missing?
- How do we explain the decision later?

NEXUSCOPE creates a single decision-support workspace. It is designed as a prototype, not an autonomous authority: human operators remain responsible for final decisions.

## Core capabilities
- Incident intake with structured and free-text reports
- AI-style extraction of entities, severity, risks and missing information
- Priority scoring with transparent factors
- Recommended response actions
- Resource allocation suggestions
- Situation timeline
- Explainable decision cards
- Tamper-evident audit chain
- Demo mode with deterministic local intelligence
- Optional OpenAI-compatible provider adapter

## Stack
- Frontend: React + Vite + TypeScript
- Backend: FastAPI + Pydantic
- Local demo intelligence: deterministic Python rules
- Optional LLM: OpenAI-compatible API endpoint
- Storage: JSON file for zero-setup demo
- Visual design: ivory / white / charcoal with restrained crimson accents

## Run

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## Optional LLM configuration
Copy `.env.example` to `.env` in `backend/` and set:
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`

The demo works without an API key.

## Demo flow
1. Open the dashboard.
2. Select a sample incident or paste a report.
3. Click "Analyze incident".
4. Review the priority explanation.
5. Inspect recommended actions and resources.
6. Open the audit panel to show integrity verification.

## Responsible-use note
This prototype is decision support. It must not be presented as a substitute for trained emergency personnel, legal authority, or professional judgement. Real deployments require validation, privacy controls, bias testing, security review, and domain-specific governance.


## One-click Windows launch
Double-click `START_NEXUSCOPE.bat`. See `RUN_ME_FIRST.txt`.
