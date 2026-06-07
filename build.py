#!/usr/bin/env python3
"""Read feature_log.tsv -> render a self-contained static index.html.
Edit feature_log.tsv (add a row), then run:  python3 build.py
Then commit + push to republish the GitHub Pages link."""
import csv, json, os, html

here = os.path.dirname(os.path.abspath(__file__))
tsv = os.path.join(here, "feature_log.tsv")
out = os.path.join(here, "index.html")

rows = []
with open(tsv, newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        r["approx"] = (r.get("approx", "0").strip() == "1")
        rows.append(r)

# newest first
rows.sort(key=lambda r: r["date"], reverse=True)
data_json = json.dumps(rows)

counts = {"daisy": 0, "skill": 0, "infra": 0}
for r in rows:
    counts[r["surface"]] = counts.get(r["surface"], 0) + 1
default_count = counts.get("daisy", 0) + counts.get("skill", 0)
total_count = len(rows)

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
    --accent:#7aa2f7; --daisy:#8b5cf6; --skill:#10b981; --infra:#64748b;
    --live:#10b981; --retired:#ef4444; --exp:#f59e0b; --prog:#3b82f6;
  }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
    font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:860px; margin:0 auto; padding:24px 16px 80px; }
  header h1 { font-size:22px; margin:0 0 4px; }
  header p { color:var(--muted); margin:0 0 20px; font-size:14px; }
  .controls { position:sticky; top:0; background:var(--bg); padding:12px 0;
    border-bottom:1px solid var(--line); z-index:5; }
  .seg { display:inline-flex; background:var(--card); border:1px solid var(--line);
    border-radius:10px; padding:3px; gap:2px; }
  .seg button { background:transparent; color:var(--muted); border:0; cursor:pointer;
    padding:7px 14px; border-radius:8px; font-size:13px; font-weight:600; }
  .seg button.on { background:var(--accent); color:#0b1020; }
  .row2 { display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; align-items:center; }
  select, input[type=search] { background:var(--card); color:var(--text);
    border:1px solid var(--line); border-radius:8px; padding:7px 10px; font-size:13px; }
  input[type=search] { flex:1; min-width:140px; }
  .count { color:var(--muted); font-size:12px; margin:14px 2px 6px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px;
    padding:14px 16px; margin-bottom:10px; }
  .top { display:flex; justify-content:space-between; gap:10px; align-items:baseline; flex-wrap:wrap; }
  .name { font-weight:700; font-size:16px; }
  .date { color:var(--muted); font-size:12px; white-space:nowrap; }
  .date .approx { opacity:.6; }
  .badges { margin:8px 0 6px; display:flex; gap:6px; flex-wrap:wrap; }
  .badge { font-size:11px; font-weight:700; padding:2px 8px; border-radius:999px;
    text-transform:uppercase; letter-spacing:.03em; }
  .b-daisy { background:rgba(139,92,246,.15); color:#c4b5fd; }
  .b-skill { background:rgba(16,185,129,.15); color:#6ee7b7; }
  .b-infra { background:rgba(100,116,139,.18); color:#cbd5e1; }
  .s-Live { background:rgba(16,185,129,.15); color:#6ee7b7; }
  .s-Retired { background:rgba(239,68,68,.15); color:#fca5a5; }
  .s-Experimental { background:rgba(245,158,11,.15); color:#fcd34d; }
  .s-In-progress { background:rgba(59,130,246,.15); color:#93c5fd; }
  .what { margin:2px 0; }
  .why { color:var(--muted); font-size:13.5px; margin:4px 0 0; }
  .why b { color:#bcc4d2; font-weight:600; }
  .loc { font:12px ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--muted);
    margin-top:8px; word-break:break-all; }
  .empty { color:var(--muted); text-align:center; padding:40px; }
  footer { color:var(--muted); font-size:12px; margin-top:30px; text-align:center; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Daisy &amp; Skills — Shipped Log</h1>
    <p>What we've built. Sister to the incident log: that one tracks what broke, this tracks what shipped.</p>
  </header>

  <div class="controls">
    <div class="seg" id="mode">
      <button data-mode="default" class="on">Daisy + skills</button>
      <button data-mode="all">Everything</button>
    </div>
    <div class="row2">
      <select id="surface">
        <option value="">All types</option>
        <option value="daisy">Daisy</option>
        <option value="skill">Skill</option>
        <option value="infra">Infra / fixes</option>
      </select>
      <select id="status">
        <option value="">Any status</option>
        <option>Live</option>
        <option>Retired</option>
        <option>Experimental</option>
        <option>In progress</option>
      </select>
      <input type="search" id="q" placeholder="Search name, what, why…">
    </div>
  </div>

  <div class="count" id="count"></div>
  <div id="list"></div>

  <footer>Backfilled from build history · edit <code>feature_log.tsv</code> + run <code>build.py</code> to update</footer>
</div>

<script>
const DATA = __DATA__;
const SURFACE_LABEL = {daisy:"Daisy", skill:"Skill", infra:"Infra"};
let mode = "default";

function esc(s){const d=document.createElement("div");d.textContent=s||"";return d.innerHTML;}

function render(){
  const surf = document.getElementById("surface").value;
  const stat = document.getElementById("status").value;
  const q = document.getElementById("q").value.trim().toLowerCase();
  let rows = DATA.slice();
  if (mode === "default") rows = rows.filter(r => r.surface !== "infra");
  if (surf) rows = rows.filter(r => r.surface === surf);
  if (stat) rows = rows.filter(r => r.status === stat);
  if (q) rows = rows.filter(r =>
    (r.name+" "+r.what+" "+r.why).toLowerCase().includes(q));

  document.getElementById("count").textContent =
    rows.length + (rows.length===1?" entry":" entries") +
    (mode==="default" ? " · Daisy + skills" : " · everything");

  const list = document.getElementById("list");
  if (!rows.length){ list.innerHTML = '<div class="empty">Nothing matches.</div>'; return; }
  list.innerHTML = rows.map(r => `
    <div class="card">
      <div class="top">
        <span class="name">${esc(r.name)}</span>
        <span class="date">${esc(r.date)}${r.approx?' <span class="approx">(approx)</span>':''}</span>
      </div>
      <div class="badges">
        <span class="badge b-${r.surface}">${esc(SURFACE_LABEL[r.surface]||r.surface)}</span>
        <span class="badge s-${esc(r.status).replace(/ /g,'-')}">${esc(r.status)}</span>
      </div>
      <div class="what">${esc(r.what)}</div>
      <div class="why"><b>Why:</b> ${esc(r.why)}</div>
      <div class="loc">${esc(r.location)}</div>
    </div>`).join("");
}

document.querySelectorAll("#mode button").forEach(b =>
  b.addEventListener("click", () => {
    mode = b.dataset.mode;
    document.querySelectorAll("#mode button").forEach(x => x.classList.remove("on"));
    b.classList.add("on");
    render();
  }));
["surface","status","q"].forEach(id =>
  document.getElementById(id).addEventListener("input", render));
render();
</script>
</body>
</html>
"""

html_out = TEMPLATE.replace("__DATA__", data_json)
with open(out, "w") as f:
    f.write(html_out)
print(f"rendered {len(rows)} rows -> {out}")
print(f"default (Daisy+skills): {default_count} · everything: {total_count}")
