# Daisy — Shipped & Incidents

Two-tab static page (GitHub Pages, noindex/link-only):
- **Shipped** — features & skills we've built (`feature_log.tsv`)
- **Incidents** — the defect log (`incident_log.tsv`)

Columns are touch-resizable and saved per-device (localStorage).

## Shipped tab — manual update
1. Edit `feature_log.tsv` (tab-separated):
   `date  name  surface  status  what  why  location  approx`
   - surface: `daisy` · `skill` · `infra` (infra hidden until the "Everything" toggle)
   - status: `Live` · `Retired` · `Experimental` · `In progress` · approx: `1` if date is a guess
2. `python3 build.py` → `git commit -am "…" && git push`

## Incidents tab — auto-synced from the Mini
The canonical defect log lives on the Mini at `~/daisy/logs/incident_log.tsv` (watchdog
auto-appends). A LaunchAgent republishes this page **whenever that file changes**:

- **Mini repo clone:** `~/daisy-changelog` (pushes via a write-scoped deploy key,
  `~/.ssh/daisy_changelog_deploy`, registered to this repo only)
- **Sync script:** `~/daisy/bin/changelog_sync.sh` — fetch+reset to origin, copy the live
  TSV in, rebuild, commit, push (with one retry on a rejected push)
- **Trigger:** `~/Library/LaunchAgents/com.daisy.changelogsync.plist`
  (`WatchPaths` on the incident log + hourly fallback + RunAtLoad)
- **Logs:** `~/daisy/logs/changelog_sync.log`

So: log/fix a defect → the row hits `incident_log.tsv` → page updates within seconds.
No action needed.

## The Drawing Board — ideas log (`/board/`)
Light "paper" card page for ideas that haven't been built yet — the forward-looking
sister to the shipped log. Lives at `board/index.html`.

1. Edit `ideas.tsv` (tab-separated):
   `date  name  domain  effort  status  pitch  notes  link  approx`
   - domain: `daisy` · `skill` · `cos` · `infra` · `work` · `life`
   - effort: `S` · `M` · `L`
   - status: `sketched` (thought through, ready to build) · `napkin` (raw idea) ·
     `shelved` (decided not now) · `built` (shipped — set `link` to `../` and add a
     row to `feature_log.tsv`)
   - default view shows sketched + napkin only; "Everything" reveals shelved + built
2. `python3 build_board.py` → `git commit -am "…" && git push`

> Note: the Mini pushes commits too. On the MacBook, `git pull` before editing
> `feature_log.tsv` to avoid a non-fast-forward.
