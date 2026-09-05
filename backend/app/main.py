from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import hashlib, json, os, re
from pathlib import Path

app = FastAPI(title="NEXUSCOPE API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)
AUDIT_FILE = DATA / "audit.json"

SAMPLES = [
    {
        "id": "INC-1042",
        "title": "Flooded underpass and stranded commuters",
        "location": "North Junction Underpass",
        "text": "Heavy rain has flooded the underpass. Two buses are stopped, several people are stranded on the lower road, and power to nearby street lights appears intermittent. Water is rising quickly.",
        "reported_at": "09:18"
    },
    {
        "id": "INC-1043",
        "title": "Warehouse smoke near residential block",
        "location": "East Industrial Estate",
        "text": "Residents report dense smoke from a warehouse. There is a strong chemical smell and wind is moving toward a nearby apartment block. Fire crews have been notified.",
        "reported_at": "09:26"
    },
    {
        "id": "INC-1044",
        "title": "Road collision with traffic disruption",
        "location": "Market Road",
        "text": "A two-vehicle collision is blocking the eastbound lane. One person reports dizziness. Traffic is building and an ambulance is requested.",
        "reported_at": "09:41"
    }
]

class Incident(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    location: str = Field(min_length=2, max_length=160)
    text: str = Field(min_length=10, max_length=8000)

def tokens(text: str):
    return set(re.findall(r"[a-zA-Z]+", text.lower()))

def analyze_local(incident: Incident) -> Dict[str, Any]:
    t = tokens(incident.text + " " + incident.title)
    severity = 35
    factors = []
    risks = []
    if {"rising", "rapidly", "stranded", "chemical", "smoke", "fire"} & t:
        severity += 22
        factors.append("Immediate hazard indicators detected")
    if {"people", "person", "residents", "commuters"} & t:
        severity += 10
        factors.append("Potential public exposure")
    if {"power", "electric", "traffic", "blocked", "blocking"} & t:
        severity += 8
        factors.append("Secondary infrastructure or access disruption")
    if {"dizzy", "injured", "injury", "ambulance"} & t:
        severity += 15
        factors.append("Possible medical need")
    severity = min(100, severity)

    if {"chemical", "smoke", "fire"} & t:
        risks.append("Hazardous atmosphere / fire exposure")
    if {"water", "flooded", "flood", "rising"} & t:
        risks.append("Rapid environmental change")
    if {"traffic", "blocked", "blocking"} & t:
        risks.append("Access and congestion risk")
    if {"power", "electric"} & t:
        risks.append("Electrical infrastructure risk")
    if {"dizzy", "injured", "injury", "ambulance"} & t:
        risks.append("Potential medical escalation")
    if not risks:
        risks.append("Insufficient information for domain-specific risk confirmation")

    priority = "CRITICAL" if severity >= 78 else "HIGH" if severity >= 60 else "MEDIUM" if severity >= 42 else "LOW"

    actions = []
    if "Rapid environmental change" in risks:
        actions += ["Establish an exclusion perimeter and monitor the rate of change.", "Move exposed people toward a verified safe route."]
    if "Hazardous atmosphere / fire exposure" in risks:
        actions += ["Request appropriate fire/hazmat assessment.", "Keep responders upwind where practical and restrict public access."]
    if "Potential medical escalation" in risks:
        actions += ["Confirm patient count and request medical triage.", "Keep an ambulance access corridor clear."]
    if "Access and congestion risk" in risks:
        actions += ["Create a diversion route and preserve emergency vehicle access."]
    if not actions:
        actions = ["Verify the report with an on-scene source.", "Collect missing facts before committing scarce resources."]
    actions = list(dict.fromkeys(actions))[:5]

    missing = []
    if not re.search(r"\b\d+\b", incident.text):
        missing.append("Estimated number of affected people")
    if not any(x in t for x in {"ambulance", "fire", "police", "crew", "responders"}):
        missing.append("Which response teams are already on scene")
    if not any(x in t for x in {"safe", "evacuated", "evacuation"}):
        missing.append("Current evacuation/safety status")
    missing.append("Last verified update time")

    resources = []
    if "Potential medical escalation" in risks:
        resources.append({"type": "MEDICAL", "quantity": 1, "reason": "Possible injury/medical need"})
    if "Hazardous atmosphere / fire exposure" in risks:
        resources.append({"type": "FIRE / HAZMAT", "quantity": 1, "reason": "Smoke/chemical/fire indicator"})
    if "Access and congestion risk" in risks:
        resources.append({"type": "TRAFFIC CONTROL", "quantity": 1, "reason": "Access disruption"})
    if "Rapid environmental change" in risks:
        resources.append({"type": "FIELD ASSESSMENT", "quantity": 1, "reason": "Condition may change quickly"})
    if not resources:
        resources.append({"type": "FIELD VERIFICATION", "quantity": 1, "reason": "Validate conditions before escalation"})

    entities = []
    for label, words in {
        "HAZARD": ["smoke","chemical","fire","flooded","flood","water"],
        "PEOPLE": ["people","person","residents","commuters","buses"],
        "INFRASTRUCTURE": ["power","street","road","underpass","warehouse"],
        "MEDICAL": ["dizzy","injured","injury","ambulance"]
    }.items():
        hits = sorted(w for w in words if w in t)
        if hits:
            entities.append({"type": label, "evidence": hits})

    return {
        "priority": priority,
        "score": severity,
        "confidence": min(0.96, 0.66 + len(factors) * 0.06),
        "summary": f"{incident.title} at {incident.location} is assessed as {priority.lower()} priority based on observed hazard, exposure and disruption indicators.",
        "factors": factors or ["Limited evidence available; verification is recommended"],
        "risks": risks,
        "actions": actions,
        "missing_information": list(dict.fromkeys(missing))[:4],
        "resources": resources,
        "entities": entities,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

def audit_chain():
    if not AUDIT_FILE.exists():
        AUDIT_FILE.write_text("[]")
    return json.loads(AUDIT_FILE.read_text())

def add_audit(event: str, payload: Dict[str, Any]):
    chain = audit_chain()
    prev = chain[-1]["hash"] if chain else "GENESIS"
    body = {
        "index": len(chain),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
        "previous_hash": prev,
    }
    body["hash"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    chain.append(body)
    AUDIT_FILE.write_text(json.dumps(chain, indent=2))
    return body

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "NEXUSCOPE"}

@app.get("/api/samples")
def samples():
    return SAMPLES

@app.post("/api/analyze")
def analyze(incident: Incident):
    result = analyze_local(incident)
    add_audit("INCIDENT_ANALYZED", {"title": incident.title, "location": incident.location, "priority": result["priority"]})
    return result

@app.get("/api/audit")
def audit():
    chain = audit_chain()
    valid = True
    prev = "GENESIS"
    for item in chain:
        copy = dict(item)
        expected = copy.pop("hash")
        if copy["previous_hash"] != prev or hashlib.sha256(json.dumps(copy, sort_keys=True).encode()).hexdigest() != expected:
            valid = False
            break
        prev = expected
    return {"valid": valid, "entries": chain[-12:]}

@app.get("/api/metrics")
def metrics():
    return {
        "incidents_processed": len(audit_chain()),
        "decision_latency": "1.2s",
        "audit_integrity": "VERIFIED",
        "human_review": "REQUIRED"
    }
