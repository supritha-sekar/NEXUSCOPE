TRACK_ID=PS07

# NEXUSCOPE — Network Incident Triage Assistant

NEXUSCOPE turns a noisy network alert stream into grouped, prioritized incidents and grounded operator actions. It uses deterministic safeguards for grouping/priority and Gemini for grounded triage reasoning. Local runbooks are retrieved with Gemini Embeddings (`gemini-embedding-001`) and cached locally; there is no hosted vector database.

## Run

Python 3.11 recommended.

```bash
pip install -r requirements.txt
python app.py
```

Open `http://localhost:8000`.

Set `GEMINI_API_KEY` before running to enable Gemini reasoning and embedding-based runbook retrieval. Never commit the key. Without a key, the app remains usable in deterministic local fallback mode and clearly labels that mode in the UI.

## Generated/local data

- `data/alerts.json` — synthetic network alert stream containing related alerts, a duplicate, an authentication burst, and a single noise alert.
- `data/runbooks/network.json` — small local troubleshooting runbook set.
- `data/runbook_embeddings.json` — generated locally on first Gemini embedding retrieval; safe to commit after generation if desired. It is not included initially because embeddings depend on the configured Gemini API.

## Architecture

1. Ingest alerts.
2. Deterministically group related alerts and isolate noise.
3. Calculate a transparent priority score.
4. Retrieve a local runbook using `gemini-embedding-001` when available, with a deterministic trigger-match fallback.
5. Send only the assembled incident facts + matched runbook to Gemini for structured reasoning.
6. Render recommendation, evidence references, retrieval method, confidence, and escalation state.

The application never claims fraud/outage/root cause as a confirmed fact and escalates when evidence or runbook coverage is insufficient.

## Demo video

Add the final demo URL here before submission.
