import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

_paused = False
_paused_lock = threading.Lock()

def is_paused():
    with _paused_lock:
        return _paused

def _set_paused(value):
    global _paused
    with _paused_lock:
        _paused = value
    socketio.emit('paused_state', {"paused": value})

@socketio.on('connect')
def handle_connect():
    emit('paused_state', {"paused": is_paused()})

@socketio.on('control_stop')
def handle_control_stop():
    _set_paused(True)

@socketio.on('control_resume')
def handle_control_resume():
    _set_paused(False)


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PGuard — Event Monitor</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#0d0f14;--surface:#161a22;--card:#1e2330;--border:#2a3040;--text:#e8eaf0;--muted:#5a6480;--accent:#4f8ef7;--green:#3dd68c;--red:#f75f5f;--yellow:#f7c948;--cyan:#38c9e0;--purple:#a78bfa}
body{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;font-size:14px;min-height:100vh}
header{background:var(--surface);border-bottom:1px solid var(--border);padding:14px 28px;display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:10px}
.dot{width:10px;height:10px;border-radius:50%;background:var(--muted);transition:all .3s}
.dot.live{background:var(--green);box-shadow:0 0 8px var(--green)}
.dot.critical{background:var(--red);box-shadow:0 0 8px var(--red);animation:pulse 1s infinite}
h1{font-size:16px;font-weight:600}
.sub{font-size:12px;color:var(--muted);margin-left:8px}
.hright{display:flex;align-items:center;gap:20px;font-size:12px;color:var(--muted)}
.badge{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:500;border:1px solid var(--border);color:var(--muted)}
.badge.live{background:rgba(61,214,140,.15);color:var(--green);border-color:rgba(61,214,140,.3)}
.badge.critical{background:rgba(247,95,95,.15);color:var(--red);border-color:rgba(247,95,95,.3);animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
main{padding:24px 28px;display:grid;gap:20px}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:14px}
.stat{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px 20px}
.stat-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px}
.stat-val{font-size:28px;font-weight:600;transition:all .3s}
.red{color:var(--red)}.green{color:var(--green)}.yellow{color:var(--yellow)}.cyan{color:var(--cyan)}
.grid2{display:grid;grid-template-columns:2fr 1fr;gap:20px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}
.panel{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.panel.cb{border-color:var(--red)}
.ph{padding:14px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.pt{font-size:13px;font-weight:500;display:flex;align-items:center;gap:8px}
.pd{font-size:11px;color:var(--muted);margin-left:4px;font-weight:400}
.pb{padding:16px 20px}
.log-scroll{max-height:280px;overflow-y:auto}
table{width:100%;border-collapse:collapse}
th{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;padding:0 0 10px;text-align:left;font-weight:500}
td{padding:7px 0;border-bottom:1px solid var(--border);font-size:12px;vertical-align:middle}
tr:last-child td{border-bottom:none}
.fl td{animation:fi .6s ease}
@keyframes fi{from{background:rgba(79,142,247,.12)}to{background:transparent}}
.ar td{background:rgba(247,95,95,.04)}
.lv{padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;letter-spacing:.4px}
.lv.INFO{background:rgba(79,142,247,.15);color:var(--accent)}
.lv.ALARM{background:rgba(247,95,95,.15);color:var(--red)}
.lv.WARN{background:rgba(247,201,72,.15);color:var(--yellow)}
.tc{color:var(--muted);font-family:monospace;width:72px}
.bl{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-bottom:6px}
.bt{height:6px;background:var(--border);border-radius:3px;overflow:hidden}
.bf{height:100%;background:var(--accent);border-radius:3px;transition:width .4s}
.bf.full{background:var(--yellow)}
.pipeline{display:flex;align-items:center;gap:6px;margin-top:14px}
.ps{flex:1;text-align:center;padding:8px 4px;border-radius:8px;font-size:11px;font-weight:500;color:var(--muted);background:var(--border);border:1px solid transparent;transition:all .3s}
.ps.active{background:rgba(79,142,247,.15);color:var(--accent);border-color:rgba(79,142,247,.3)}
.ps.done{background:rgba(61,214,140,.1);color:var(--green);border-color:rgba(61,214,140,.3)}
.pa{color:var(--muted);font-size:12px}
.sl{display:flex;flex-direction:column;gap:10px;max-height:260px;overflow-y:auto}
.si{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:12px 14px;animation:fi .6s ease}
.sm{display:flex;justify-content:space-between;margin-bottom:6px}
.si-idx{font-size:11px;font-weight:600;color:var(--green)}
.si-time{font-size:11px;color:var(--muted)}
.si-text{font-size:13px;line-height:1.6}
.empty{font-size:13px;color:var(--muted);font-style:italic;padding:8px 0}
.ad{display:flex;flex-direction:column;gap:10px}
.af label{font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);display:block;margin-bottom:3px}
.af span{font-size:13px}
.cb-banner{background:rgba(247,95,95,.1);border:1px solid rgba(247,95,95,.3);border-radius:8px;padding:10px 14px;font-size:12px;color:var(--red);font-weight:500;margin-top:12px;animation:pulse 1s infinite}
.al{max-height:160px;overflow-y:auto}
footer{padding:14px 28px;border-top:1px solid var(--border);font-size:11px;color:var(--muted);display:flex;justify-content:space-between}
.report-btn{background:rgba(79,142,247,.12);color:var(--accent);border:1px solid rgba(79,142,247,.3);border-radius:6px;padding:3px 10px;font-size:11px;font-weight:500;cursor:pointer;transition:all .2s}
.report-btn:hover{background:rgba(79,142,247,.22)}
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(5,6,10,.7);z-index:100;align-items:center;justify-content:center;padding:24px}
.modal-overlay.open{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:12px;width:100%;max-width:640px;max-height:85vh;display:flex;flex-direction:column;overflow:hidden}
.modal-h{padding:16px 22px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.modal-h h2{font-size:14px;font-weight:600}
.modal-close{background:none;border:none;color:var(--muted);font-size:18px;cursor:pointer;line-height:1;padding:4px}
.modal-close:hover{color:var(--text)}
.modal-body{padding:18px 22px;overflow-y:auto}
.modal-section-label{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);margin:0 0 8px}
.modal-log-table{width:100%;border-collapse:collapse;margin-bottom:22px}
.modal-log-table td{padding:6px 0;border-bottom:1px solid var(--border);font-size:12px}
.modal-summary-box{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px;font-size:13px;line-height:1.6}
.hcontrols{display:flex;gap:8px;margin-right:6px}
.ctrl-btn{background:var(--surface);border:1px solid var(--border);color:var(--text);padding:5px 12px;border-radius:6px;font-size:12px;font-weight:500;cursor:pointer;transition:all .2s}
.ctrl-btn:hover{background:var(--card)}
.ctrl-btn.stop{color:var(--red);border-color:rgba(247,95,95,.3)}
.ctrl-btn.resume{color:var(--green);border-color:rgba(61,214,140,.3);display:none}
.badge.paused{background:rgba(247,201,72,.15);color:var(--yellow);border-color:rgba(247,201,72,.3)}
.modal.wide{max-width:720px}
</style>
</head>
<body>
<header>
  <div class="logo">
    <div class="dot" id="robot-dot"></div>
    <h1>PGuard Event Monitor</h1>
    <span class="sub">IA004 — Event Summarization using LLMs</span>
  </div>
  <div class="hright">
    <div class="hcontrols">
      <button class="ctrl-btn" onclick="openAllLogs()">All logs</button>
      <button class="ctrl-btn" onclick="openAllSummaries()">All summaries</button>
      <button class="ctrl-btn stop" id="stop-btn" onclick="stopWork()">Stop</button>
      <button class="ctrl-btn resume" id="resume-btn" onclick="resumeWork()">Resume</button>
    </div>
    <span id="clock">--:--:--</span>
    <span>Last msg: <span id="last-msg">—</span></span>
    <span class="badge" id="sys-badge">Idle</span>
  </div>
</header>
<main>
  <div class="stats">
    <div class="stat"><div class="stat-label">Messages received</div><div class="stat-val" id="s-total">0</div></div>
    <div class="stat"><div class="stat-label">Alarms detected</div><div class="stat-val red" id="s-alarms">0</div></div>
    <div class="stat"><div class="stat-label">Warnings</div><div class="stat-val yellow" id="s-warns">0</div></div>
    <div class="stat"><div class="stat-label">Summaries made</div><div class="stat-val green" id="s-sums">0</div></div>
    <div class="stat"><div class="stat-label">Session time</div><div class="stat-val cyan" id="s-time">0m 0s</div></div>
  </div>
  <div class="grid2">
    <div class="panel">
      <div class="ph">
        <div class="pt"><div class="dot live" style="width:7px;height:7px"></div>Live log feed<span class="pd">/robot/events</span></div>
        <span class="badge live">Listening</span>
      </div>
      <div class="pb"><div class="log-scroll"><table><thead><tr><th style="width:72px">Time</th><th style="width:70px">Level</th><th>Message</th></tr></thead><tbody id="log-body"><tr><td colspan="3" class="empty">Waiting for robot events...</td></tr></tbody></table></div></div>
    </div>
    <div class="panel" id="alarm-panel">
      <div class="ph"><div class="pt"><div class="dot" style="width:7px;height:7px;background:var(--red)"></div>Alarm panel</div><span class="badge" id="alarm-badge">Clear</span></div>
      <div class="pb" id="alarm-body"><div class="empty">No alarms detected yet.</div></div>
    </div>
  </div>
  <div class="grid3">
    <div class="panel" style="grid-column:span 2">
      <div class="ph"><div class="pt"><div class="dot" style="width:7px;height:7px;background:var(--purple)"></div>LLM pipeline</div><span class="badge" id="llm-badge">Waiting</span></div>
      <div class="pb">
        <div class="bl"><span>Buffer</span><span id="buf-count">0 / 5</span></div>
        <div class="bt"><div class="bf" id="buf-fill" style="width:0%"></div></div>
        <div class="pipeline">
          <div class="ps" id="p1">Receive</div><div class="pa">›</div>
          <div class="ps" id="p2">Collect</div><div class="pa">›</div>
          <div class="ps" id="p3">Summarize</div><div class="pa">›</div>
          <div class="ps" id="p4">Reset</div>
        </div>
      </div>
    </div>
    <div class="panel">
      <div class="ph"><div class="pt"><div class="dot" style="width:7px;height:7px;background:var(--red)"></div>Alert log</div></div>
      <div class="pb"><div class="al"><table><thead><tr><th style="width:72px">Time</th><th>Event</th></tr></thead><tbody id="alert-body"><tr><td colspan="2" class="empty">No alerts yet</td></tr></tbody></table></div></div>
    </div>
  </div>
  <div class="panel">
    <div class="ph"><div class="pt"><div class="dot" style="width:7px;height:7px;background:var(--green)"></div>LLM summaries</div><span style="font-size:11px;color:var(--muted)" id="sum-meta">Waiting for first batch...</span></div>
    <div class="pb"><div class="sl" id="sum-list"><div class="empty">Summaries appear here every 5 messages.</div></div></div>
  </div>
</main>
<footer>
  <span>PGuard Security Robotics — IA004 Event Summarization Dashboard</span>
  <span>Enova Robotics internship project</span>
</footer>
<div class="modal-overlay" id="report-modal">
  <div class="modal">
    <div class="modal-h">
      <h2 id="report-title">Report — Summary</h2>
      <button class="modal-close" onclick="closeModal('report-modal')">✕</button>
    </div>
    <div class="modal-body">
      <p class="modal-section-label">Messages included</p>
      <table class="modal-log-table"><tbody id="report-logs"></tbody></table>
      <p class="modal-section-label">Summary</p>
      <div class="modal-summary-box" id="report-summary"></div>
    </div>
  </div>
</div>
<div class="modal-overlay" id="alllogs-modal">
  <div class="modal wide">
    <div class="modal-h">
      <h2>All logs received</h2>
      <button class="modal-close" onclick="closeModal('alllogs-modal')">✕</button>
    </div>
    <div class="modal-body" id="alllogs-body"></div>
  </div>
</div>
<div class="modal-overlay" id="allsummaries-modal">
  <div class="modal wide">
    <div class="modal-h">
      <h2>All summaries</h2>
      <button class="modal-close" onclick="closeModal('allsummaries-modal')">✕</button>
    </div>
    <div class="modal-body" id="allsummaries-body"></div>
  </div>
</div>
<script>
const socket=io();
const reports={};
const allLogs=[];
function closeModal(id){document.getElementById(id).classList.remove('open');}
['report-modal','alllogs-modal','allsummaries-modal'].forEach(id=>{
  document.getElementById(id).addEventListener('click',e=>{if(e.target.id===id)closeModal(id);});
});
function openReport(idx){
  const r=reports[idx];
  if(!r)return;
  document.getElementById('report-title').textContent='Report — Summary #'+idx;
  document.getElementById('report-summary').textContent=r.text;
  const tbody=document.getElementById('report-logs');
  tbody.innerHTML='';
  (r.logs||[]).forEach(line=>{
    const m=line.match(/(\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(.*)/);
    const tr=document.createElement('tr');
    if(m){
      tr.innerHTML='<td class="tc" style="width:72px">'+m[1]+'</td><td style="width:70px"><span class="lv '+m[2]+'">'+m[2]+'</span></td><td>'+m[3]+'</td>';
    }else{
      tr.innerHTML='<td colspan="3">'+line+'</td>';
    }
    tbody.appendChild(tr);
  });
  document.getElementById('report-modal').classList.add('open');
}
function buildSummaryItem(idx,data){
  const item=document.createElement('div');item.className='si';
  item.innerHTML='<div class="sm"><span class="si-idx">Summary #'+idx+'</span><span style="display:flex;align-items:center;gap:10px"><span class="si-time">'+data.time+'</span><button class="report-btn" onclick="openReport('+idx+')">Report</button></span></div><div class="si-text">'+data.text+'</div>';
  return item;
}
function openAllSummaries(){
  const body=document.getElementById('allsummaries-body');
  body.innerHTML='';
  const idxs=Object.keys(reports).map(Number).sort((a,b)=>b-a);
  if(idxs.length===0){body.innerHTML='<div class="empty">No summaries yet.</div>';}
  else{
    const wrap=document.createElement('div');wrap.className='sl';wrap.style.maxHeight='none';
    idxs.forEach(idx=>wrap.appendChild(buildSummaryItem(idx,reports[idx])));
    body.appendChild(wrap);
  }
  document.getElementById('allsummaries-modal').classList.add('open');
}
function openAllLogs(){
  const body=document.getElementById('alllogs-body');
  body.innerHTML='';
  if(allLogs.length===0){body.innerHTML='<div class="empty">No logs yet.</div>';}
  else{
    const table=document.createElement('table');table.className='modal-log-table';
    const tbody=document.createElement('tbody');
    for(let i=allLogs.length-1;i>=0;i--){
      const d=allLogs[i];
      const tr=document.createElement('tr');
      tr.innerHTML='<td class="tc" style="width:72px">'+d.time+'</td><td style="width:70px"><span class="lv '+d.level+'">'+d.level+'</span></td><td>'+d.message+'</td>';
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);body.appendChild(table);
  }
  document.getElementById('alllogs-modal').classList.add('open');
}
function stopWork(){socket.emit('control_stop');}
function resumeWork(){socket.emit('control_resume');}
socket.on('paused_state',data=>{
  document.getElementById('stop-btn').style.display=data.paused?'none':'inline-block';
  document.getElementById('resume-btn').style.display=data.paused?'inline-block':'none';
  const badge=document.getElementById('sys-badge');
  if(data.paused){badge.textContent='Paused';badge.className='badge paused';}
});
let total=0,alarms=0,warns=0,sums=0,start=Date.now(),alarmTimes=[],critical=false;
function pad(n){return String(n).padStart(2,'0')}
setInterval(()=>{
  const e=Math.floor((Date.now()-start)/1000),m=Math.floor(e/60),s=e%60;
  document.getElementById('s-time').textContent=m+'m '+s+'s';
  const n=new Date();
  document.getElementById('clock').textContent=pad(n.getHours())+':'+pad(n.getMinutes())+':'+pad(n.getSeconds());
},1000);
socket.on('log',data=>{
  total++;document.getElementById('s-total').textContent=total;
  allLogs.push(data);
  document.getElementById('last-msg').textContent=data.time;
  document.getElementById('robot-dot').className='dot live';
  document.getElementById('sys-badge').textContent='Live';document.getElementById('sys-badge').className='badge live';
  if(data.level==='ALARM'){
    alarms++;document.getElementById('s-alarms').textContent=alarms;
    alarmTimes.push(Date.now());alarmTimes=alarmTimes.filter(t=>Date.now()-t<=120000);
    if(alarmTimes.length>=3)triggerCritical();
    updateAlarmPanel(data);addAlertLog(data);
  }
  if(data.level==='WARN'){warns++;document.getElementById('s-warns').textContent=warns;}
  addLogRow(data);
  setStep('p1','active');setTimeout(()=>{setStep('p1','done');setStep('p2','active');},300);setTimeout(()=>setStep('p2','done'),700);
});
socket.on('buffer',data=>{
  const pct=Math.round((data.current/data.total)*100);
  document.getElementById('buf-fill').style.width=pct+'%';
  document.getElementById('buf-fill').className='bf'+(data.current>=data.total?' full':'');
  document.getElementById('buf-count').textContent=data.current+' / '+data.total;
});
socket.on('pipeline',data=>{
  const map={receiving:0,collecting:1,summarizing:2,done:3,idle:-1};
  const active=map[data.stage]??-1;
  ['p1','p2','p3','p4'].forEach((id,i)=>{document.getElementById(id).className='ps'+(i<active?' done':i===active?' active':'');});
  const b=document.getElementById('llm-badge');
  if(data.stage==='summarizing'){b.textContent='Processing';b.className='badge live';}
  else if(data.stage==='idle'){b.textContent='Waiting';b.className='badge';}
  else if(data.stage==='done'){b.textContent='Done';b.className='badge live';}
});
socket.on('summary',data=>{
  sums++;document.getElementById('s-sums').textContent=sums;
  reports[sums]=data;
  document.getElementById('sum-meta').textContent=sums+' summaries generated';
  const list=document.getElementById('sum-list');
  if(list.querySelector('.empty'))list.innerHTML='';
  list.prepend(buildSummaryItem(sums,data));
  while(list.children.length>5)list.removeChild(list.lastChild);
});
function addLogRow(data){
  const tbody=document.getElementById('log-body');
  if(tbody.querySelector('.empty'))tbody.innerHTML='';
  const tr=document.createElement('tr');
  tr.className=(data.level==='ALARM'?'ar ':'')+'fl';
  tr.innerHTML='<td class="tc">'+data.time+'</td><td><span class="lv '+data.level+'">'+data.level+'</span></td><td>'+data.message+'</td>';
  tbody.prepend(tr);while(tbody.children.length>15)tbody.removeChild(tbody.lastChild);
}
function addAlertLog(data){
  const tbody=document.getElementById('alert-body');
  if(tbody.querySelector('.empty'))tbody.innerHTML='';
  const tr=document.createElement('tr');
  tr.innerHTML='<td class="tc">'+data.time+'</td><td style="color:var(--red)">'+data.message+'</td>';
  tbody.prepend(tr);
}
function updateAlarmPanel(data){
  document.getElementById('alarm-body').innerHTML='<div class="ad"><div class="af"><label>Time</label><span>'+data.time+'</span></div><div class="af"><label>Event</label><span style="color:var(--red);font-weight:500">'+data.message+'</span></div><div class="af"><label>Total alarms</label><span style="color:var(--red)">'+alarms+'</span></div>'+(critical?'<div class="cb-banner">3+ alarms in 2 minutes — operator action required</div>':'<div style="font-size:12px;color:var(--muted);margin-top:4px">Operator action required.</div>')+'</div>';
  document.getElementById('alarm-badge').textContent='Alert';document.getElementById('alarm-badge').className='badge critical';
  document.getElementById('alarm-panel').classList.add('cb');
}
function triggerCritical(){
  critical=true;document.getElementById('robot-dot').className='dot critical';
  document.getElementById('sys-badge').textContent='CRITICAL';document.getElementById('sys-badge').className='badge critical';
}
function setStep(id,state){document.getElementById(id).className='ps'+(state?' '+state:'');}
</script>
</body>
</html>"""

@app.route('/')
def index():
    return render_template_string(HTML)

def emit_log(timestamp, level, message):
    socketio.emit('log', {"time": timestamp, "level": level, "message": message})

def emit_buffer(current, total):
    socketio.emit('buffer', {"current": current, "total": total})

def emit_pipeline(stage):
    socketio.emit('pipeline', {"stage": stage})

def emit_summary(text, time, logs=None):
    socketio.emit('summary', {"text": text, "time": time, "logs": logs or []})

def run_server():
    socketio.run(app, host='0.0.0.0', port=5000)

def start_server():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
