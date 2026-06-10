#!/usr/bin/env python3
"""Read feature_log.tsv + incident_log.tsv -> render a self-contained static index.html.
Two tabs: Shipped (features) and Incidents (defects). Columns are touch-resizable and
persisted per-device via localStorage.

Edit feature_log.tsv (or let the Mini sync incident_log.tsv), then run: python3 build.py
Then commit + push to republish the GitHub Pages link."""
import csv, json, os, datetime

here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, "index.html")

def short_date(iso):
    try:
        d = datetime.date.fromisoformat(iso.strip())
        return f"{d.month}/{d.day}/{str(d.year)[2:]}"
    except Exception:
        return iso

# ---- features ----
features = []
with open(os.path.join(here, "feature_log.tsv"), newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        r["approx"] = (r.get("approx", "0").strip() == "1")
        r["disp_date"] = short_date(r["date"])
        features.append(r)
features.sort(key=lambda r: r["date"], reverse=True)

# ---- incidents (skip # comment lines; real header = date cause mode symptom resolution) ----
incidents = []
ipath = os.path.join(here, "incident_log.tsv")
if os.path.exists(ipath):
    with open(ipath, newline="") as f:
        lines = [ln for ln in f if not ln.lstrip().startswith("#")]
    for r in csv.DictReader(lines, delimiter="\t"):
        if not r.get("date"):
            continue
        r["disp_date"] = short_date(r["date"])
        incidents.append(r)
    incidents.sort(key=lambda r: r["date"], reverse=True)

feat_json = json.dumps(features)
inc_json = json.dumps(incidents)
default_count = sum(1 for r in features if r["surface"] != "infra")

# build timestamp (manual format — avoid platform %-m strftime differences)
_now = datetime.datetime.now()
_h12 = _now.hour % 12 or 12
_ampm = "AM" if _now.hour < 12 else "PM"
built_stamp = f"{_now.month}/{_now.day}/{str(_now.year)[2:]} {_h12}:{_now.minute:02d} {_ampm}"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Daisy — Shipped & Incidents</title>
<style>
  :root { --bg:#0f1115; --card:#171a21; --line:#262b36; --text:#e7eaf0; --muted:#9aa3b2; --accent:#7aa2f7; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
    font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:1100px; margin:0 auto; padding:16px 12px 60px; }
  h1 { font-size:19px; margin:0 0 2px; }
  .sub { color:var(--muted); margin:0 0 12px; font-size:12.5px; }
  .sub a.board { color:var(--accent); font-weight:600; text-decoration:none; }
  .sub a.board:hover { text-decoration:underline; }
  .tabs { display:inline-flex; background:var(--card); border:1px solid var(--line);
    border-radius:10px; padding:3px; gap:2px; margin-bottom:14px; }
  .tabs button { background:transparent; color:var(--muted); border:0; cursor:pointer;
    padding:7px 16px; border-radius:8px; font-size:13px; font-weight:600; }
  .tabs button.on { background:var(--accent); color:#0b1020; }
  .hdr { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
  .refresh { background:var(--accent); color:#0b1020; border:0; border-radius:9px;
    padding:8px 14px; font-size:13px; font-weight:700; cursor:pointer; white-space:nowrap; }
  .refresh:active { opacity:.75; }
  .built { display:block; margin-top:3px; opacity:.75; font-size:11.5px; }
  .controls { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:8px; }
  .seg { display:inline-flex; background:var(--card); border:1px solid var(--line);
    border-radius:9px; padding:3px; gap:2px; }
  .seg button { background:transparent; color:var(--muted); border:0; cursor:pointer;
    padding:6px 12px; border-radius:7px; font-size:12.5px; font-weight:600; }
  .seg button.on { background:var(--accent); color:#0b1020; }
  select, input[type=search], .reset { background:var(--card); color:var(--text);
    border:1px solid var(--line); border-radius:8px; padding:6px 9px; font-size:12.5px; }
  input[type=search] { flex:1; min-width:120px; }
  .reset { cursor:pointer; color:var(--muted); }
  .legend { color:var(--muted); font-size:11.5px; margin:0 0 8px; }
  .count { color:var(--muted); font-size:12px; margin:2px 2px 8px; }
  .scroll { overflow-x:auto; border:1px solid var(--line); border-radius:10px;
    -webkit-overflow-scrolling:touch; }
  table { border-collapse:collapse; table-layout:fixed; font-size:12.5px; }
  thead th { position:relative; background:#1c2029; color:var(--muted); text-align:left;
    font-weight:600; padding:6px 8px; border-bottom:1px solid var(--line);
    white-space:nowrap; overflow:hidden; }
  td { padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; overflow:hidden; }
  tbody tr:hover { background:#1b1f28; }
  .c-date { white-space:nowrap; color:var(--muted); font-variant-numeric:tabular-nums; }
  .c-date .ap { opacity:.55; }
  .c-name { font-weight:700; }
  .clamp { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
  .c-why { color:var(--muted); }
  .badge { font-size:10.5px; font-weight:700; padding:2px 7px; border-radius:999px;
    text-transform:uppercase; letter-spacing:.03em; white-space:nowrap; }
  .b-daisy { background:rgba(139,92,246,.16); color:#c4b5fd; }
  .b-skill { background:rgba(16,185,129,.16); color:#6ee7b7; }
  .b-infra { background:rgba(100,116,139,.20); color:#cbd5e1; }
  .s-Live { background:rgba(16,185,129,.16); color:#6ee7b7; }
  .s-Retired { background:rgba(239,68,68,.16); color:#fca5a5; }
  .s-Experimental { background:rgba(245,158,11,.16); color:#fcd34d; }
  .s-In-progress { background:rgba(59,130,246,.16); color:#93c5fd; }
  .cz { font-weight:800; font-size:12px; padding:2px 8px; border-radius:7px; }
  .cz-A { background:rgba(239,68,68,.16); color:#fca5a5; }
  .cz-B { background:rgba(245,158,11,.16); color:#fcd34d; }
  .cz-C { background:rgba(139,92,246,.16); color:#c4b5fd; }
  .cz-D { background:rgba(59,130,246,.16); color:#93c5fd; }
  .cz-E { background:rgba(100,116,139,.22); color:#cbd5e1; }
  .m-auto { background:rgba(16,185,129,.16); color:#6ee7b7; }
  .m-manual { background:rgba(100,116,139,.22); color:#cbd5e1; }
  .empty { color:var(--muted); text-align:center; padding:30px; }
  .rz { position:absolute; top:0; right:-7px; width:16px; height:100%;
    cursor:col-resize; touch-action:none; z-index:3; }
  .rz:after { content:""; position:absolute; right:7px; top:18%; height:64%; width:2px;
    background:var(--line); border-radius:2px; }
  .rz:active:after, .rz:hover:after { background:var(--accent); }
  footer { color:var(--muted); font-size:11.5px; margin-top:16px; }
  .hidden { display:none; }
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div>
      <h1>Daisy — Shipped &amp; Incidents</h1>
      <p class="sub">Drag a column's right edge to resize — widths save on this device. Incidents update automatically when a defect is logged.<span class="built">Page built __BUILT__ · tap Refresh to pull the latest published version. · <a class="board" href="board/">✏️ Drawing Board</a></span></p>
    </div>
    <button class="refresh" id="refresh" title="Reload the latest published page">↻ Refresh</button>
  </div>

  <div class="tabs" id="tabs">
    <button data-tab="shipped" class="on">Shipped</button>
    <button data-tab="incidents">Incidents</button>
  </div>

  <!-- ===== SHIPPED ===== -->
  <section id="t-shipped">
    <div class="controls">
      <div class="seg" id="mode">
        <button data-mode="default" class="on">Daisy + skills</button>
        <button data-mode="all">Everything</button>
      </div>
      <select id="f-status">
        <option value="">Any status</option>
        <option>Live</option><option>Retired</option>
        <option>Experimental</option><option>In progress</option>
      </select>
      <input type="search" id="f-q" placeholder="Search…">
      <button class="reset" data-reset="shipped">Reset widths</button>
    </div>
    <div class="count" id="c-shipped"></div>
    <div class="scroll">
      <table id="tbl-shipped">
        <colgroup><col><col><col><col><col><col></colgroup>
        <thead><tr>
          <th>Date<span class="rz" data-i="0"></span></th>
          <th>Feature<span class="rz" data-i="1"></span></th>
          <th>What it does<span class="rz" data-i="2"></span></th>
          <th>Why<span class="rz" data-i="3"></span></th>
          <th>Surface<span class="rz" data-i="4"></span></th>
          <th>Status<span class="rz" data-i="5"></span></th>
        </tr></thead>
        <tbody id="rows-shipped"></tbody>
      </table>
    </div>
  </section>

  <!-- ===== INCIDENTS ===== -->
  <section id="t-incidents" class="hidden">
    <div class="controls">
      <select id="i-cause">
        <option value="">Any cause</option>
        <option value="A">A · auth</option>
        <option value="B">B · poller</option>
        <option value="C">C · TUI/ghost-text</option>
        <option value="D">D · plugin outbound</option>
        <option value="E">E · host/infra</option>
      </select>
      <select id="i-mode">
        <option value="">Any mode</option>
        <option value="auto">auto (self-healed)</option>
        <option value="manual">manual fix</option>
      </select>
      <input type="search" id="i-q" placeholder="Search…">
      <button class="reset" data-reset="incidents">Reset widths</button>
    </div>
    <div class="legend">Cause: <b>A</b> auth · <b>B</b> poller · <b>C</b> TUI/ghost-text · <b>D</b> plugin outbound · <b>E</b> host/infra &nbsp;|&nbsp; Mode: auto = watchdog self-recovered, manual = hands-on fix</div>
    <div class="count" id="c-incidents"></div>
    <div class="scroll">
      <table id="tbl-incidents">
        <colgroup><col><col><col><col><col></colgroup>
        <thead><tr>
          <th>Date<span class="rz" data-i="0"></span></th>
          <th>Cause<span class="rz" data-i="1"></span></th>
          <th>Mode<span class="rz" data-i="2"></span></th>
          <th>Symptom<span class="rz" data-i="3"></span></th>
          <th>Resolution<span class="rz" data-i="4"></span></th>
        </tr></thead>
        <tbody id="rows-incidents"></tbody>
      </table>
    </div>
  </section>

  <footer>Shipped: edit <code>feature_log.tsv</code> + run <code>build.py</code>. Incidents: auto-synced from the Mini's <code>incident_log.tsv</code>.</footer>
</div>

<script>
const FEAT = __FEAT__;
const INC = __INC__;
const SL = {daisy:"Daisy", skill:"Skill", infra:"Infra"};
function esc(s){const d=document.createElement("div");d.textContent=s||"";return d.innerHTML;}

/* ---- generic resizable/persisted columns for one table ---- */
function makeResizable(tableId, defaults, key){
  const table = document.getElementById(tableId);
  const cols = table.querySelectorAll("colgroup col");
  let widths;
  try { const s = JSON.parse(localStorage.getItem(key));
    widths = (Array.isArray(s) && s.length === defaults.length) ? s.map(Number) : defaults.slice();
  } catch(e) { widths = defaults.slice(); }
  function apply(){ let t=0; widths.forEach((w,i)=>{ cols[i].style.width=w+"px"; t+=w; }); table.style.width=t+"px"; }
  function save(){ try{ localStorage.setItem(key, JSON.stringify(widths)); }catch(e){} }
  let drag=null;
  table.querySelectorAll(".rz").forEach(h=>{
    h.addEventListener("pointerdown", e=>{ e.preventDefault(); e.stopPropagation();
      drag={i:+h.dataset.i, x:e.clientX, w:widths[+h.dataset.i]}; h.setPointerCapture(e.pointerId); });
    h.addEventListener("pointermove", e=>{ if(!drag) return;
      widths[drag.i]=Math.max(40, drag.w+(e.clientX-drag.x)); apply(); });
    const end=()=>{ if(drag){ drag=null; save(); } };
    h.addEventListener("pointerup", end); h.addEventListener("pointercancel", end);
  });
  apply();
  return { reset(){ widths=defaults.slice(); apply(); save(); } };
}
const RS = {
  shipped: makeResizable("tbl-shipped", [56,104,250,210,78,84], "daisylog_colw_v2"),
  incidents: makeResizable("tbl-incidents", [56,62,74,260,260], "daisyinc_colw_v1"),
};
document.querySelectorAll(".reset").forEach(b =>
  b.addEventListener("click", () => RS[b.dataset.reset].reset()));

/* ---- shipped render ---- */
let mode = "default";
function renderShipped(){
  const stat = document.getElementById("f-status").value;
  const q = document.getElementById("f-q").value.trim().toLowerCase();
  let r = FEAT.slice();
  if (mode === "default") r = r.filter(x => x.surface !== "infra");
  if (stat) r = r.filter(x => x.status === stat);
  if (q) r = r.filter(x => (x.name+" "+x.what+" "+x.why).toLowerCase().includes(q));
  document.getElementById("c-shipped").textContent =
    r.length + (r.length===1?" entry":" entries") + (mode==="default"?" · Daisy + skills":" · everything");
  const tb = document.getElementById("rows-shipped");
  tb.innerHTML = !r.length ? '<tr><td colspan="6" class="empty">Nothing matches.</td></tr>' :
    r.map(x => `<tr>
      <td class="c-date">${esc(x.disp_date)}${x.approx?' <span class="ap">~</span>':''}</td>
      <td class="c-name"><div class="clamp">${esc(x.name)}</div></td>
      <td><div class="clamp">${esc(x.what)}</div></td>
      <td class="c-why"><div class="clamp">${esc(x.why)}</div></td>
      <td><span class="badge b-${x.surface}">${esc(SL[x.surface]||x.surface)}</span></td>
      <td><span class="badge s-${esc(x.status).replace(/ /g,'-')}">${esc(x.status)}</span></td>
    </tr>`).join("");
}
document.querySelectorAll("#mode button").forEach(b =>
  b.addEventListener("click", () => { mode=b.dataset.mode;
    document.querySelectorAll("#mode button").forEach(x=>x.classList.remove("on"));
    b.classList.add("on"); renderShipped(); }));
["f-status","f-q"].forEach(id => document.getElementById(id).addEventListener("input", renderShipped));

/* ---- incidents render ---- */
function renderIncidents(){
  const cause = document.getElementById("i-cause").value;
  const md = document.getElementById("i-mode").value;
  const q = document.getElementById("i-q").value.trim().toLowerCase();
  let r = INC.slice();
  if (cause) r = r.filter(x => (x.cause||"").toUpperCase() === cause);
  if (md) r = r.filter(x => (x.mode||"").toLowerCase() === md);
  if (q) r = r.filter(x => (x.symptom+" "+x.resolution).toLowerCase().includes(q));
  document.getElementById("c-incidents").textContent = r.length + (r.length===1?" incident":" incidents");
  const tb = document.getElementById("rows-incidents");
  tb.innerHTML = !r.length ? '<tr><td colspan="5" class="empty">Nothing matches.</td></tr>' :
    r.map(x => { const c=(x.cause||"").toUpperCase(), m=(x.mode||"").toLowerCase();
      return `<tr>
      <td class="c-date">${esc(x.disp_date)}</td>
      <td><span class="cz cz-${esc(c)}">${esc(c)}</span></td>
      <td><span class="badge m-${esc(m)}">${esc(x.mode)}</span></td>
      <td><div class="clamp">${esc(x.symptom)}</div></td>
      <td class="c-why"><div class="clamp">${esc(x.resolution)}</div></td>
    </tr>`; }).join("");
}
["i-cause","i-mode","i-q"].forEach(id => document.getElementById(id).addEventListener("input", renderIncidents));

/* ---- tabs ---- */
document.querySelectorAll("#tabs button").forEach(b =>
  b.addEventListener("click", () => {
    const t = b.dataset.tab;
    document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("on"));
    b.classList.add("on");
    document.getElementById("t-shipped").classList.toggle("hidden", t!=="shipped");
    document.getElementById("t-incidents").classList.toggle("hidden", t!=="incidents");
  }));

/* ---- refresh: cache-busted reload so a fresh publish shows immediately ---- */
document.getElementById("refresh").addEventListener("click", () => {
  location.replace(location.pathname + "?t=" + Date.now());
});

renderShipped();
renderIncidents();
</script>
</body>
</html>
"""

html = (TEMPLATE.replace("__FEAT__", feat_json).replace("__INC__", inc_json)
        .replace("__BUILT__", built_stamp))
with open(out, "w") as f:
    f.write(html)
print(f"rendered {len(features)} features (default {default_count}) + {len(incidents)} incidents -> {out}")
