# Session Log

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-07-20
> Append-only — never edit past entries.

| Date | Summary |
|------|---------|
| 2026-07-20 | Initialized `.project-knowledge/` for this pre-existing project (CREATE mode — no prior `PROJECT_KNOWLEDGE.md`). Scanned and documented the existing 4-step AI job pipeline (agent.py + server.py + ui/index.html), its JSON-file "schema", routes, and systems. No code changes made. |
| 2026-07-20 → 2026-07-21 | First real end-to-end test run with the candidate's actual resume — fixed a locally-broken `claude` CLI install (native binary missing, recurred ~4x this session due to an unrelated auto-updater flakiness on this machine) and set up `.venv`/`.env` (`FIRECRAWL_API_KEY`, `EXA_API_KEY`). Added Exa as a fallback for pages Firecrawl can't scrape (LinkedIn/Reddit). Reworked the dashboard substantially: resume-driven role selection ("Find Roles" → checkboxes), free-text-via-chips run preferences (employment type/pay/location) folded into search + scoring, job source badges, list/grid view toggle with bottom-pinned action buttons, a step-based UI flow (setup → running → results, with Cancel), and a "dodge the red flags" canvas mini-game shown while the pipeline runs. Fixed `run_claude()` to surface `claude` CLI exec failures as a readable error instead of a raw JSON-parse crash in the UI. 40 tests passing (up from 29). |
