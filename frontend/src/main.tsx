import React,{useEffect,useState} from "react";
import {createRoot} from "react-dom/client";
import {ShieldCheck,Activity,MapPin,AlertTriangle,BrainCircuit,Clock3,FileCheck2,ChevronRight,RefreshCw} from "lucide-react";
import "./styles.css";

const API="http://localhost:8000/api";
type Sample={id:string,title:string,location:string,text:string,reported_at:string};
type Result={priority:string,score:number,confidence:number,summary:string,factors:string[],risks:string[],actions:string[],missing_information:string[],resources:{type:string,quantity:number,reason:string}[],entities:{type:string,evidence:string[]}[]};

function Badge({children,kind=""}:{children:React.ReactNode,kind?:string}){return <span className={"badge "+kind}>{children}</span>}
function App(){
 const [samples,setSamples]=useState<Sample[]>([]),[selected,setSelected]=useState<Sample|null>(null);
 const [title,setTitle]=useState(""),[location,setLocation]=useState(""),[text,setText]=useState("");
 const [result,setResult]=useState<Result|null>(null),[audit,setAudit]=useState<any>(null),[loading,setLoading]=useState(false);
 useEffect(()=>{fetch(API+"/samples").then(r=>r.json()).then(setSamples); fetch(API+"/audit").then(r=>r.json()).then(setAudit)},[]);
 const load=(s:Sample)=>{setSelected(s);setTitle(s.title);setLocation(s.location);setText(s.text);setResult(null)}
 const analyze=async()=>{setLoading(true);const r=await fetch(API+"/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title,location,text})});setResult(await r.json());setLoading(false);fetch(API+"/audit").then(r=>r.json()).then(setAudit)}
 return <div className="app">
  <header><div className="brand"><div className="mark"><ShieldCheck size={22}/></div><div><b>NEXUSCOPE</b><small>AI INCIDENT INTELLIGENCE</small></div></div>
   <div className="header-right"><span className="live"><i/> DEMO SYSTEM ONLINE</span><span className="human">Human review required</span></div>
  </header>
  <main>
   <section className="hero"><div><div className="eyebrow">DECISION SUPPORT / 01</div><h1>From raw reports to<br/><em>clearer decisions.</em></h1><p>Transform fragmented incident information into explainable priorities, response actions and resource recommendations.</p></div>
    <div className="hero-stat"><Activity/><strong>1.2s</strong><span>analysis latency</span></div>
   </section>
   <div className="grid">
    <aside className="panel queue"><div className="panel-head"><div><span className="eyebrow">INCOMING</span><h2>Incident queue</h2></div><Badge>LIVE</Badge></div>
     {samples.map(s=><button className={"incident "+(selected?.id===s.id?"active":"")} onClick={()=>load(s)} key={s.id}><div className="inc-top"><span>{s.id}</span><Clock3 size={14}/><span>{s.reported_at}</span></div><strong>{s.title}</strong><div className="muted"><MapPin size={13}/>{s.location}</div><ChevronRight size={17}/></button>)}
    </aside>
    <section className="panel workspace"><div className="panel-head"><div><span className="eyebrow">ANALYSIS WORKSPACE</span><h2>Incident brief</h2></div><button className="ghost" onClick={()=>{setResult(null);setTitle("");setLocation("");setText("")}}><RefreshCw size={14}/> Reset</button></div>
     <div className="form"><label>Incident title<input value={title} onChange={e=>setTitle(e.target.value)} placeholder="e.g. Flooded underpass"/></label><label>Location<input value={location} onChange={e=>setLocation(e.target.value)} placeholder="Area / facility / road"/></label>
     <label className="full">Raw report<textarea value={text} onChange={e=>setText(e.target.value)} placeholder="Paste the report, call summary or field observation here..."/></label></div>
     <button className="primary" disabled={loading||text.length<10} onClick={analyze}><BrainCircuit size={18}/>{loading?"Analyzing intelligence…":"Analyze with NEXUSCOPE"}<ChevronRight size={18}/></button>
     {result&&<div className="result">
      <div className="priority-card"><div><span className="eyebrow">RECOMMENDED PRIORITY</span><div className="priority"><span className={"dot "+result.priority.toLowerCase()}/>{result.priority}</div><p>{result.summary}</p></div><div className="score"><strong>{result.score}</strong><span>/ 100</span><small>{Math.round(result.confidence*100)}% confidence</small></div></div>
      <div className="cards"><Card title="Why this priority"><ul>{result.factors.map(x=><li key={x}>{x}</li>)}</ul></Card><Card title="Detected risks"><div className="chips">{result.risks.map(x=><Badge key={x}>{x}</Badge>)}</div></Card><Card title="Recommended actions"><ol>{result.actions.map(x=><li key={x}>{x}</li>)}</ol></Card><Card title="Information gaps"><ul>{result.missing_information.map(x=><li key={x}>{x}</li>)}</ul></Card></div>
      <div className="resource"><div><span className="eyebrow">RESOURCE PLAN</span><h3>Suggested deployment</h3></div>{result.resources.map(r=><div className="res" key={r.type}><b>{r.quantity}× {r.type}</b><span>{r.reason}</span></div>)}</div>
     </div>}
    </section>
   </div>
   <section className="bottom-grid">
    <div className="panel"><div className="panel-head"><div><span className="eyebrow">TRACEABILITY</span><h2>Decision audit</h2></div><Badge kind={audit?.valid?"ok":"danger"}>{audit?.valid?"CHAIN VERIFIED":"CHECK FAILED"}</Badge></div>
     <div className="audit-line"><FileCheck2 size={19}/><div><b>Tamper-evident event chain</b><span>Every analysis writes a hash-linked audit event for review.</span></div><strong>{audit?.entries?.length||0}</strong></div>
    </div>
    <div className="panel impact"><div className="panel-head"><div><span className="eyebrow">IMPACT MODEL</span><h2>Why this is different</h2></div></div><div className="impact-row"><span>01</span><b>Explainable</b><p>Every priority has visible evidence and factors.</p></div><div className="impact-row"><span>02</span><b>Operational</b><p>Moves beyond chat into actions and resource planning.</p></div><div className="impact-row"><span>03</span><b>Accountable</b><p>Decisions remain auditable and human-controlled.</p></div></div>
   </section>
  </main>
  <footer>NEXUSCOPE • Prototype for NexusTiQ24 • Built for responsible GenAI decision support</footer>
 </div>
}
function Card({title,children}:{title:string,children:React.ReactNode}){return <div className="mini"><span className="eyebrow">{title}</span>{children}</div>}
createRoot(document.getElementById("root")!).render(<App/>)
