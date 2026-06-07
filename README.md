# Daisy & Skills — Shipped Log

Sister to the Daisy incident log. The incident log tracks what *broke*; this tracks what *shipped*.

Live page (noindex, link-only): see repo Pages URL.

## How to update
1. Edit `feature_log.tsv` — add a row (tab-separated). Columns:
   `date  name  surface  status  what  why  location  approx`
   - **surface:** `daisy` · `skill` · `infra` (infra hidden in default view, shown by the "Everything" toggle)
   - **status:** `Live` · `Retired` · `Experimental` · `In progress`
   - **approx:** `1` if the date is an estimate, else `0`
2. Run `python3 build.py` (regenerates `index.html`).
3. `git commit -am "log: <feature>" && git push` — Pages updates in ~1 min.

`seed.py` was the one-time backfill from MEMORY.md and isn't needed again.
