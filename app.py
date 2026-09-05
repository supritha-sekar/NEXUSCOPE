import json, os
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from backend.incident_engine import analyze_alerts, load_json

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; DIST=ROOT/"frontend"/"dist"

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(DIST),**kw)
    def send_json(self,code,obj):
        body=json.dumps(obj,indent=2).encode()
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def get_runbooks(self):
        out=[]
        for p in sorted((DATA/"runbooks").glob("*.json")): out += load_json(p)
        return out
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/health": return self.send_json(200,{"status":"ok","track":"PS07","app":"NEXUSCOPE"})
        if path=="/api/alerts": return self.send_json(200,load_json(DATA/"alerts.json"))
        if path=="/api/runbooks": return self.send_json(200,self.get_runbooks())
        if path=="/api/analyze": return self.send_json(200,analyze_alerts(load_json(DATA/"alerts.json"),self.get_runbooks()))
        return super().do_GET()
    def do_POST(self):
        if urlparse(self.path).path!="/api/analyze": return self.send_json(404,{"error":"Not found"})
        try:
            n=int(self.headers.get("Content-Length","0")); payload=json.loads(self.rfile.read(n) or b"{}")
            return self.send_json(200,analyze_alerts(payload.get("alerts",[]),self.get_runbooks()))
        except Exception as e: return self.send_json(400,{"error":str(e)})

if __name__=="__main__":
    ThreadingHTTPServer(("0.0.0.0",int(os.getenv("PORT","8000"))),Handler).serve_forever()
