#!/usr/bin/env python3
"""Read ideas.tsv -> render the Drawing Board (board/index.html).
Light "paper" aesthetic, card layout — the forward-looking sister page to the
dark shipped/incidents log.

Edit ideas.tsv, then run: python3 build_board.py
Then commit + push to republish."""
import csv, json, os, datetime

here = os.path.dirname(os.path.abspath(__file__))
outdir = os.path.join(here, "board")
os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "index.html")

def short_date(iso):
    try:
        d = datetime.date.fromisoformat(iso.strip())
        return f"{d.month}/{d.day}/{str(d.year)[2:]}"
    except Exception:
        return iso

ideas = []
with open(os.path.join(here, "ideas.tsv"), newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if not r.get("date"):
            continue
        r["approx"] = (r.get("approx", "0").strip() == "1")
        r["disp_date"] = short_date(r["date"])
        ideas.append(r)

# sort: sketched first, then napkin, then shelved, then built; newest first within each
ORDER = {"sketched": 0, "napkin": 1, "shelved": 2, "built": 3}
ideas.sort(key=lambda r: (ORDER.get(r["status"], 9), r["date"]), reverse=False)
ideas.sort(key=lambda r: r["date"], reverse=True)
ideas.sort(key=lambda r: ORDER.get(r["status"], 9))

ideas_json = json.dumps(ideas)

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
<title>The Drawing Board</title>
<style>
  :root { --bg:#faf8f3; --card:#ffffff; --line:#e4e0d6; --text:#2b2a26; --muted:#8a8578;
    --pencil:#5f6b7a; --shadow:0 1px 3px rgba(60,55,40,.08); }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
    font:14.5px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
  .wrap { max-width:860px; margin:0 auto; padding:18px 14px 60px; }
  .hdr { display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
  h1 { font-size:21px; margin:0 0 1px; letter-spacing:-.01em; }
  .sub { color:var(--muted); margin:0 0 14px; font-size:12.5px; font-style:italic; }
  .built { display:block; margin-top:3px; opacity:.8; font-size:11px; font-style:normal; }
  .refresh { background:var(--pencil); color:#fff; border:0; border-radius:9px;
    padding:8px 14px; font-size:13px; font-weight:700; cursor:pointer; white-space:nowrap; }
  .refresh:active { opacity:.75; }
  .controls { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-bottom:12px; }
  .seg { display:inline-flex; background:var(--card); border:1px solid var(--line);
    border-radius:9px; padding:3px; gap:2px; box-shadow:var(--shadow); }
  .seg button { background:transparent; color:var(--muted); border:0; cursor:pointer;
    padding:6px 12px; border-radius:7px; font-size:12.5px; font-weight:600; }
  .seg button.on { background:var(--pencil); color:#fff; }
  select, input[type=search] { background:var(--card); color:var(--text);
    border:1px solid var(--line); border-radius:8px; padding:7px 9px; font-size:12.5px;
    box-shadow:var(--shadow); }
  input[type=search] { flex:1; min-width:120px; }
  .count { color:var(--muted); font-size:12px; margin:0 2px 10px; }
  .grid { display:grid; grid-template-columns:1fr; gap:10px; }
  @media (min-width:640px) { .grid { grid-template-columns:1fr 1fr; } }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px;
    padding:13px 14px 11px; box-shadow:var(--shadow); }
  .card.napkin { border-style:dashed; background:#fffdf7; }
  .card.shelved { opacity:.62; }
  .card.built { background:#f4f9f4; border-color:#cfe3cf; }
  .top { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:6px; }
  .chip { font-size:10.5px; font-weight:800; padding:3px 9px; border-radius:999px;
    text-transform:uppercase; letter-spacing:.05em; white-space:nowrap; }
  .st-sketched { background:#eef2f7; color:#3d5a80; }
  .st-napkin { background:#fdf3dc; color:#9a6b1f; }
  .st-shelved { background:#eceae4; color:#8a8578; }
  .st-built { background:#e2f0e2; color:#2f7d3b; }
  .meta { font-size:11px; color:var(--muted); font-weight:600; white-space:nowrap; }
  .b-daisy { color:#7c5cd6; } .b-skill { color:#1f9d6e; } .b-cos { color:#b3771d; }
  .b-infra { color:#5f6b7a; } .b-work { color:#2868b5; } .b-life { color:#c2527e; }
  .name { font-weight:750; font-size:15.5px; margin:0 0 4px; }
  .pitch { margin:0 0 6px; font-size:13.5px; }
  .notes { margin:0; color:var(--muted); font-size:12px; }
  .foot { display:flex; justify-content:space-between; align-items:center; margin-top:8px; }
  .date { font-size:10.5px; color:var(--muted); font-variant-numeric:tabular-nums; }
  .date .ap { opacity:.6; }
  .go { font-size:11.5px; font-weight:700; color:#2f7d3b; text-decoration:none; }
  .empty { color:var(--muted); text-align:center; padding:36px 12px; grid-column:1/-1;
    font-style:italic; }
  a.backlink { color:var(--pencil); font-weight:600; text-decoration:none; font-size:12px; }
  a.backlink:hover { text-decoration:underline; }
  footer { color:var(--muted); font-size:11.5px; margin-top:18px; }
  footer code { background:#f1eee6; padding:1px 5px; border-radius:5px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div>
      <h1>&#9999;&#65039; The Drawing Board</h1>
      <p class="sub">sketches, not blueprints — ideas waiting to be built
        <span class="built">Page built __BUILT__ · <a class="backlink" href="../">&larr; Shipped &amp; Incidents</a></span></p>
    </div>
    <button class="refresh" id="refresh" title="Reload the latest published page">&#8635; Refresh</button>
  </div>

  <div class="controls">
    <div class="seg" id="mode">
      <button data-mode="active" class="on">Active</button>
      <button data-mode="all">Everything</button>
    </div>
    <select id="f-domain">
      <option value="">Any area</option>
      <option value="cos">Chief of Staff</option>
      <option value="daisy">Daisy</option>
      <option value="skill">Skill</option>
      <option value="infra">Infra</option>
      <option value="work">Work</option>
      <option value="life">Life</option>
    </select>
    <select id="f-effort">
      <option value="">Any size</option>
      <option value="S">S — small</option>
      <option value="M">M — medium</option>
      <option value="L">L — large</option>
    </select>
    <input type="search" id="f-q" placeholder="Search&hellip;">
  </div>
  <div class="count" id="count"></div>
  <div class="grid" id="grid"></div>

  <footer>Statuses: <b>Sketched</b> = thought through, ready to build &middot; <b>Napkin</b> = raw idea &middot; <b>Shelved</b> = decided not now &middot; <b>Built</b> = shipped (see the shipped log).<br>
  Edit <code>ideas.tsv</code> + run <code>build_board.py</code> to update.</footer>
</div>

<script>
const IDEAS = __IDEAS__;
const DL = {daisy:"Daisy", skill:"Skill", cos:"CoS", infra:"Infra", work:"Work", life:"Life"};
const STL = {sketched:"&#9999;&#65039; Sketched", napkin:"&#128221; Napkin",
             shelved:"&#128452;&#65039; Shelved", built:"&#9989; Built"};
function esc(s){const d=document.createElement("div");d.textContent=s||"";return d.innerHTML;}

let mode = "active";
function render(){
  const dom = document.getElementById("f-domain").value;
  const eff = document.getElementById("f-effort").value;
  const q = document.getElementById("f-q").value.trim().toLowerCase();
  let r = IDEAS.slice();
  if (mode === "active") r = r.filter(x => x.status === "sketched" || x.status === "napkin");
  if (dom) r = r.filter(x => x.domain === dom);
  if (eff) r = r.filter(x => x.effort === eff);
  if (q) r = r.filter(x => (x.name+" "+x.pitch+" "+x.notes).toLowerCase().includes(q));
  document.getElementById("count").textContent =
    r.length + (r.length===1?" idea":" ideas") + (mode==="active"?" on the board":" · everything");
  document.getElementById("grid").innerHTML = !r.length ?
    '<div class="empty">Nothing on the board.</div>' :
    r.map(x => `<div class="card ${esc(x.status)}">
      <div class="top">
        <span class="chip st-${esc(x.status)}">${STL[x.status]||esc(x.status)}</span>
        <span class="meta"><span class="b-${esc(x.domain)}">${esc(DL[x.domain]||x.domain)}</span> &middot; ${esc(x.effort)}</span>
      </div>
      <p class="name">${esc(x.name)}</p>
      <p class="pitch">${esc(x.pitch)}</p>
      ${x.notes ? `<p class="notes">${esc(x.notes)}</p>` : ""}
      <div class="foot">
        <span class="date">${esc(x.disp_date)}${x.approx?' <span class="ap">~</span>':''}</span>
        ${x.link ? `<a class="go" href="${esc(x.link)}">&rarr; shipped log</a>` : ""}
      </div>
    </div>`).join("");
}
document.querySelectorAll("#mode button").forEach(b =>
  b.addEventListener("click", () => { mode=b.dataset.mode;
    document.querySelectorAll("#mode button").forEach(x=>x.classList.remove("on"));
    b.classList.add("on"); render(); }));
["f-domain","f-effort","f-q"].forEach(id =>
  document.getElementById(id).addEventListener("input", render));
document.getElementById("refresh").addEventListener("click", () => {
  location.replace(location.pathname + "?t=" + Date.now());
});
render();
</script>
</body>
</html>
"""

html = TEMPLATE.replace("__IDEAS__", ideas_json).replace("__BUILT__", built_stamp)
with open(out, "w") as f:
    f.write(html)
active = sum(1 for r in ideas if r["status"] in ("sketched", "napkin"))
print(f"rendered {len(ideas)} ideas ({active} active) -> {out}")
