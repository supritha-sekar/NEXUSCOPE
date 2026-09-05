import json
import math
import os
from pathlib import Path
from typing import Any

try:
    from google import genai
except Exception:
    genai = None

ROOT = Path(__file__).resolve().parents[1]
EMBED_CACHE = ROOT / "data" / "runbook_embeddings.json"
EMBED_MODEL = "gemini-embedding-001"
LLM_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _client():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or genai is None:
        return None
    return genai.Client(api_key=key)


def related(a, b):
    if a.get("device") == b.get("device"):
        return True
    if a.get("site") == b.get("site") and {a.get("type"), b.get("type")} & {"LINK_DOWN", "DEVICE_UNREACHABLE"}:
        return True
    if {a.get("type"), b.get("type")} <= {"LINK_DOWN", "DEVICE_UNREACHABLE", "HIGH_LATENCY"}:
        return True
    return False


def group_alerts(alerts):
    groups, used = [], set()
    for i, a in enumerate(alerts):
        if i in used:
            continue
        group = [a]
        used.add(i)
        changed = True
        while changed:
            changed = False
            for j, b in enumerate(alerts):
                if j not in used and any(related(x, b) for x in group):
                    group.append(b)
                    used.add(j)
                    changed = True
        groups.append(group)
    return groups


def _runbook_text(rb):
    return "\n".join([
        rb.get("title", ""),
        "Triggers: " + ", ".join(rb.get("trigger_types", [])),
        "Initial response: " + rb.get("initial_response", ""),
        "Steps: " + " | ".join(rb.get("steps", [])),
    ])


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _embed(client, text):
    result = client.models.embed_content(model=EMBED_MODEL, contents=text)
    values = getattr(result.embeddings[0], "values", None)
    return list(values or [])


def _load_embedding_cache():
    if not EMBED_CACHE.exists():
        return {}
    try:
        return load_json(EMBED_CACHE)
    except Exception:
        return {}


def _save_embedding_cache(cache):
    EMBED_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(EMBED_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def retrieve_runbook(group, runbooks, client=None):
    """Retrieve the best local runbook. Gemini embeddings are preferred; lexical matching is the safe fallback."""
    if not runbooks:
        return None, "NO_RUNBOOKS", 0.0

    query = "\n".join(
        f"{a.get('type', '')} {a.get('device', '')} {a.get('site', '')} {a.get('description', '')}"
        for a in group
    )

    if client:
        try:
            cache = _load_embedding_cache()
            query_vec = _embed(client, query)
            scored = []
            for rb in runbooks:
                key = rb["id"]
                if key not in cache:
                    cache[key] = _embed(client, _runbook_text(rb))
                scored.append((_cosine(query_vec, cache[key]), rb))
            _save_embedding_cache(cache)
            scored.sort(key=lambda x: x[0], reverse=True)
            score, rb = scored[0]
            # A semantic match is useful only when it is supported by the runbook trigger types.
            types = {a.get("type") for a in group}
            trigger_match = bool(types & set(rb.get("trigger_types", [])))
            if trigger_match and score >= 0.30:
                return rb, "GEMINI_EMBEDDING", round(score, 3)
        except Exception:
            pass

    # Deterministic, local fallback keeps the app usable when Gemini is unavailable.
    types = {a.get("type") for a in group}
    for rb in runbooks:
        if types & set(rb.get("trigger_types", [])):
            return rb, "LOCAL_TRIGGER_MATCH", 0.0
    return None, "NO_MATCH", 0.0


def _deterministic_incident(group, runbooks, client=None, idx=1):
    types = {a.get("type") for a in group}
    score = 35
    reasons = []
    if "LINK_DOWN" in types:
        score += 25
        reasons.append("A network link is down.")
    if "DEVICE_UNREACHABLE" in types:
        score += 20
        reasons.append("A network device is unreachable.")
    if "HIGH_LATENCY" in types:
        score += 10
        reasons.append("Latency is elevated.")
    if "AUTH_FAILURE_BURST" in types:
        score += 10
        reasons.append("Authentication failures are occurring in a burst.")
    score = min(score, 100)
    priority = "CRITICAL" if score >= 90 else "HIGH" if score >= 70 else "MEDIUM"

    rb, retrieval_method, retrieval_score = retrieve_runbook(group, runbooks, client)
    return {
        "incident_id": f"INC-{idx:03d}",
        "title": rb["title"] if rb else f"Uncovered network incident {idx}",
        "priority": priority,
        "score": score,
        "confidence": 0.92 if rb else 0.61,
        "alerts": group,
        "alert_count": len(group),
        "reasons": reasons,
        "runbook_id": rb["id"] if rb else None,
        "runbook_status": "RUNBOOK_MATCH" if rb else "ESCALATE",
        "retrieval_method": retrieval_method,
        "retrieval_score": retrieval_score,
        "recommended_action": rb["initial_response"] if rb else "Escalate to a human network engineer with the assembled alert context.",
        "evidence": rb["steps"] if rb else [],
        "escalate": not bool(rb),
        "human_decision": "Review and approve" if rb else "Required",
        "gemini_used": False,
        "gemini_reasoning": None,
    }


def _gemini_reason(client, incident):
    runbook = {
        "id": incident["runbook_id"],
        "title": incident["title"],
        "steps": incident["evidence"],
        "recommended_action": incident["recommended_action"],
    }
    prompt = f"""You are a network incident triage assistant. You must reason ONLY from the supplied alert evidence and runbook. Do not diagnose, invent missing facts, or claim an outage cause is confirmed.

Incident facts:
{json.dumps({k: incident[k] for k in ['incident_id','priority','score','alerts','reasons']}, indent=2)}

Matched local runbook:
{json.dumps(runbook, indent=2)}

Return ONLY valid JSON with these keys:
- reasoning: 2-4 concise sentences explaining why the alerts belong together and why the priority is justified.
- recommended_action: a concise operator action based only on the runbook.
- evidence_refs: array of alert IDs and/or runbook step numbers supporting the recommendation.
- escalation_reason: string; empty if the runbook adequately covers the case.
- confidence: number from 0 to 1.

If evidence is insufficient or the runbook does not cover the situation, set escalation_reason and do not invent a response."""
    response = client.models.generate_content(
        model=LLM_MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json", "temperature": 0.1},
    )
    text = getattr(response, "text", "") or ""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Gemini returned a non-object response")
    return data


def analyze_alerts(alerts, runbooks):
    client = _client()
    incidents, noise = [], []
    idx = 0
    for group in group_alerts(alerts):
        if len(group) == 1 and group[0].get("type") == "AUTH_FAILURE":
            noise += group
            continue
        idx += 1
        incident = _deterministic_incident(group, runbooks, client=client, idx=idx)

        if client and incident["runbook_id"]:
            try:
                ai = _gemini_reason(client, incident)
                incident["recommended_action"] = ai.get("recommended_action") or incident["recommended_action"]
                incident["gemini_reasoning"] = ai.get("reasoning")
                incident["evidence_refs"] = ai.get("evidence_refs", [])
                incident["escalation_reason"] = ai.get("escalation_reason", "")
                incident["confidence"] = min(0.99, max(0.0, float(ai.get("confidence", incident["confidence"]))))
                incident["escalate"] = bool(incident["escalation_reason"])
                incident["human_decision"] = "Required" if incident["escalate"] else "Review and approve"
                incident["runbook_status"] = "GEMINI_GROUNDED" if not incident["escalate"] else "ESCALATE"
                incident["gemini_used"] = True
            except Exception as exc:
                incident["gemini_error"] = str(exc)[:180]

        incidents.append(incident)

    incidents.sort(key=lambda x: x["score"], reverse=True)
    return {
        "track": "PS07",
        "incidents": incidents,
        "noise": noise,
        "ai": {
            "gemini_available": bool(client),
            "model": LLM_MODEL if client else None,
            "embedding_model": EMBED_MODEL if client else None,
            "mode": "Gemini + local deterministic safeguards" if client else "Local deterministic fallback (set GEMINI_API_KEY for AI reasoning)",
        },
        "summary": {
            "alerts_received": len(alerts),
            "incidents_created": len(incidents),
            "noise_alerts": len(noise),
            "critical": sum(x["priority"] == "CRITICAL" for x in incidents),
            "high": sum(x["priority"] == "HIGH" for x in incidents),
            "runbook_grounded": sum(bool(x["runbook_id"]) for x in incidents),
            "escalations": sum(x["escalate"] for x in incidents),
            "gemini_grounded": sum(x["gemini_used"] for x in incidents),
        },
    }
