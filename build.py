#!/usr/bin/env python3
"""Read feature_log.tsv -> render a self-contained static index.html (compact scroll table
with touch-resizable, localStorage-persisted column widths).
Edit feature_log.tsv (add a row), then run:  python3 build.py
Then commit + push to republish the GitHub Pages link."""
import csv, json, os, datetime

here = os.path.dirname(os.path.abspath(__file__))
tsv = os.path.join(here, "feature_log.tsv")
out = os.path.join(here, "index.html")

def short_date(iso):
    try:
        d = datetime.date.fromisoformat(iso)
        return f"{d.month}/{d.day}/{str(d.year)[2:]}"
    except Exception:
        return iso

rows = []
with open(tsv, newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        r["approx"] = (r.get("approx", "0").strip() == "1")
        r["disp_date"] = short_date(r["date"])
        rows.append(r)

rows.sort(key=lambda r: r["date"], reverse=True)
data_json = json.dumps(rows)

total_count = len(rows)
default_count = sum(1 for r in rows if r["surface"] != "infra")

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Daisy & Skills — Shipped Log</title>
<style>
  :root {
    --bg:#0f1115; --card:#171a21; --line:#262b36; --text:#e7eaf0; --muted:#9aa3b2;
    --accent:#7aa2f7;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
    font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:1100px; margin:0 auto; padding:16px 12px 60px; }
  h1 { font-size:19px; margin:0 0 2px; }
  .sub { color:var(--muted); margin:0 0 12px; font-size:12.5px; }
  .controls { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:10px; }
  .seg { display:inline-flex; background:var(--card); border:1px solid var(--line);
    border-radius:9px; padding:3px; gap:2px; }
  .seg button { background:transparent; color:var(--muted); border:0; cursor:pointer;
    padding:6px 12px; border-radius:7px; font-size:12.5px; font-weight:600; }
  .seg button.on { background:var(--accent); color:#0b1020; }
  select, input[type=search], #reset { background:var(--card); color:var(--text);
    border:1px solid var(--line); border-radius:8px; padding:6px 9px; font-size:12.5px; }
  input[type=search] { flex:1; min-width:120px; }
  #reset { cursor:pointer; color:var(--muted); }
  .count { color:var(--muted); font-size:12px; margin:2px 2px 8px; }
  .scroll { overflow-x:auto; border:1px solid var(--line); border-radius:10px;
    -webkit-overflow-scrolling:touch; }
  table { border-collapse:collapse; table-layout:fixed; font-size:12.5px; }
  thead th { position:relative; background:#1c2029; color:var(--muted);
    text-align:left; font-weight:600; padding:6px 8px; border-bottom:1px solid var(--line);
    white-space:nowrap; overflow:hidden; }
  td { padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top;
    overflow:hidden; }
  tbody tr:hover { background:#1b1f28; }
  .c-date { white-space:nowrap; color:var(--muted); font-variant-numeric:tabular-nums; }
  .c-date .ap { opacity:.55; }
  .c-name { font-weight:700; }
  .clamp { display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
    overflow:hidden; }
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
  /* drag handle for resizing a column */
  .rz { position:absolute; top:0; right:-7px; width:16px; height:100%;
    cursor:col-resize; touch-action:none; z-index:3; }
  .rz:after { content:""; position:absolute; right:7px; top:18%; height:64%; width:2px;
    background:var(--line); border-radius:2px; }
  .rz:active:after, .rz:hover:after { background:var(--accent); }
  .empty { color:var(--muted); text-align:center; padding:30px; }
  footer { color:var(--muted); font-size:11.5px; margin-top:16px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>Daisy &amp; Skills — Shipped Log</h1>
  <p class="sub">Drag a column's right edge to resize — your widths save on this phone and stick next time.</p>

  <div class="controls">
    <div class="seg" id="mode">
      <button data-mode="default" class="on">Daisy + skills</button>
      <button data-mode="all">Everything</button>
    </div>
    <select id="status">
      <option value="">Any status</option>
      <option>Live</option><option>Retired</option>
      <option>Experimental</option><option>In progress</option>
    </select>
    <input type="search" id="q" placeholder="Search…">
    <button id="reset">Reset widths</button>
  </div>

  <div class="count" id="count"></div>

  <div class="scroll">
    <table>
      <colgroup><col><col><col><col><col><col></colgroup>
      <thead><tr>
        <th>Date<span class="rz" data-i="0"></span></th>
        <th>Feature<span class="rz" data-i="1"></span></th>
        <th>What it does<span class="rz" data-i="2"></span></th>
        <th>Why<span class="rz" data-i="3"></span></th>
        <th>Surface<span class="rz" data-i="4"></span></th>
        <th>Status<span class="rz" data-i="5"></span></th>
      </tr></thead>
      <tbody id="rows"></tbody>
    </table>
  </div>

  <footer>Edit <code>feature_log.tsv</code> + run <code>build.py</code> to update.</footer>
</div>

<script>
const DATA = __DATA__;
const SL = {daisy:"Daisy", skill:"Skill", infra:"Infra"};
let mode = "default";
function esc(s){const d=document.createElement("div");d.textContent=s||"";return d.innerHTML;}

/* ---- resizable, persisted column widths ---- */
const DEF = [56, 104, 250, 210, 78, 84];
const KEY = "daisylog_colw_v1";
const cols = document.querySelectorAll("colgroup col");
const table = document.querySelector(".scroll table");
let widths = loadW();
function loadW(){
  try { const s = JSON.parse(localStorage.getItem(KEY));
    if (Array.isArray(s) && s.length === 6) return s.map(Number); } catch(e){}
  return DEF.slice();
}
function saveW(){ try { localStorage.setItem(KEY, JSON.stringify(widths)); } catch(e){} }
function applyW(){
  let tot = 0;
  widths.forEach((w,i)=>{ cols[i].style.width = w + "px"; tot += w; });
  table.style.width = tot + "px";
}
let drag = null;
document.querySelectorAll(".rz").forEach(h => {
  h.addEventListener("pointerdown", e => {
    e.preventDefault(); e.stopPropagation();
    const i = +h.dataset.i;
    drag = { i, x: e.clientX, w: widths[i] };
    h.setPointerCapture(e.pointerId);
  });
  h.addEventListener("pointermove", e => {
    if (!drag) return;
    widths[drag.i] = Math.max(40, drag.w + (e.clientX - drag.x));
    applyW();
  });
  const end = () => { if (drag) { drag = null; saveW(); } };
  h.addEventListener("pointerup", end);
  h.addEventListener("pointercancel", end);
});
document.getElementById("reset").addEventListener("click", () => {
  widths = DEF.slice(); applyW(); saveW();
});

/* ---- filtering + render ---- */
function render(){
  const stat = document.getElementById("status").value;
  const q = document.getElementById("q").value.trim().toLowerCase();
  let r = DATA.slice();
  if (mode === "default") r = r.filter(x => x.surface !== "infra");
  if (stat) r = r.filter(x => x.status === stat);
  if (q) r = r.filter(x => (x.name+" "+x.what+" "+x.why).toLowerCase().includes(q));

  document.getElementById("count").textContent =
    r.length + (r.length===1?" entry":" entries") +
    (mode==="default" ? " · Daisy + skills" : " · everything");

  const tb = document.getElementById("rows");
  if (!r.length){ tb.innerHTML = '<tr><td colspan="6" class="empty">Nothing matches.</td></tr>'; return; }
  tb.innerHTML = r.map(x => `
    <tr>
      <td class="c-date">${esc(x.disp_date)}${x.approx?' <span class="ap">~</span>':''}</td>
      <td class="c-name"><div class="clamp">${esc(x.name)}</div></td>
      <td><div class="clamp">${esc(x.what)}</div></td>
      <td class="c-why"><div class="clamp">${esc(x.why)}</div></td>
      <td><span class="badge b-${x.surface}">${esc(SL[x.surface]||x.surface)}</span></td>
      <td><span class="badge s-${esc(x.status).replace(/ /g,'-')}">${esc(x.status)}</span></td>
    </tr>`).join("");
}

document.querySelectorAll("#mode button").forEach(b =>
  b.addEventListener("click", () => {
    mode = b.dataset.mode;
    document.querySelectorAll("#mode button").forEach(x => x.classList.remove("on"));
    b.classList.add("on"); render();
  }));
["status","q"].forEach(id => document.getElementById(id).addEventListener("input", render));

applyW();
render();
</script>
</body>
</html>
"""

with open(out, "w") as f:
    f.write(TEMPLATE.replace("__DATA__", data_json))
print(f"rendered {len(rows)} rows -> {out}")
print(f"default (Daisy+skills): {default_count} · everything: {total_count}")
