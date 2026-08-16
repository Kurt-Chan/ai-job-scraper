# Features & Workflows

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-08-16

## Features

- **Resume-driven role selection** — clicking "Find Roles" runs `analyze_resume()` and shows the candidate's 4–6 derived target roles as checkboxes (default all checked) so the user picks which roles this specific run should search for, instead of always searching everything. Nothing profession-specific is hardcoded — see `CLAUDE.md`.
- **Search preferences (chips)** — before starting a search, the user can pick Employment Type (Full-time/Part-time/Contract/Freelance/Hourly, multi-select), Pay/Currency (USD/EUR/GBP, multi-select), and Location — a "Worldwide Remote" checkbox or a free-text country field, mutually exclusive (`onWorldwideToggle()`/`updateLocationDependentUI()` in `ui/index.html`: checking one clears/disables the other) so they can't combine into a widening OR like `"Worldwide Remote or India"`. A "Local currency" chip is disabled until a country is typed, then its label and the value sent both become e.g. `"Local currency (Egypt)"` — no ambiguous "local" left for Claude to infer. These get assembled client-side into one natural-language preferences string (e.g. `"Egypt, Part-time or Hourly work, paid in USD or Local currency (Egypt)"`) sent to `/api/run` and folded into both `prompts/build_queries.md` (search targeting) and `prompts/analyze.md` (scoring). Note: the location field is a targeting instruction, not an exclusion — typing a country searches *for* it, there's no "avoid this region" concept. Selections persist in `localStorage`.
- **Configurable search sources** — `config.json` lets the user edit `job_boards` and `reddit_groups` (with optional `extra_terms`) without touching code or prompts.
- **Discover + scrape pipeline** — search results are deduped by canonical URL (regional/`www.` subdomains collapsed), interleaved round-robin across queries, then each candidate page is scraped: Firecrawl first, Exa as a fallback for pages Firecrawl can't reach (LinkedIn, Reddit), then the search snippet as a last resort.
- **AI scoring** — every scraped posting scored 0–100 against the resume and any run preferences (skills, seniority, remote signals, freshness, red flags, location/pay/employment-type fit); only score ≥ 60 kept, verdict `apply | review | skip`.
- **Auto cover letters** — for every `apply`-verdict job at/above `THRESHOLD` (70), Claude drafts a 1–2 paragraph plain-text cover letter using a suggested framing angle.
- **Tailored CVs (Typst → PDF → ATS check)** — for the same `apply`-verdict jobs that get a cover letter, Claude writes a full Typst CV aimed at that posting, using `resume.md` for content and `templates/cv.typ` for styling. `agent.py` writes `output/cvs/<slug>.typ`, compiles it with the `typst` binary, then runs `pdftotext` on the result and warns if the text layer is nearly empty, has no email, or spills past one page. The prompt forbids inventing anything not in the resume — tailoring is selection and phrasing only. Downloadable from each job card via `GET /api/cv`.
- **Drafter-reviewer apply stage** — the Apply button on a job card opens a modal and streams a three-phase run: Claude drafts a cover letter grounded strictly in `resume.md`, a second fresh-context call reviews it for invented claims and requirement coverage, then the reviewer's edits are applied mechanically. The modal shows the initial draft and the revised letter side by side, plus a coverage table (matched/bridged/gap) and any claims the reviewer couldn't find in the resume. In testing it caught a fabricated "four years" (the resume says 2021–present) and an Airtable overclaim. Everything is archived under `output/applications/<slug>/`.
- **"Find more jobs"** — a search turns up far more pages than one run scrapes (46–168 seen in practice, 20 scraped). Rather than discarding the rest, every discovered page is saved to `output/page_queue.json` and the button scrapes the *next* batch on demand: no repeated search, no page scraped twice, and cover letters/CVs already written are skipped rather than regenerated. Keeps a second look cheaper than a second run.
- **Per-domain scrape cap** — no single site may take more than `MAX_PAGES_PER_DOMAIN` (3) slots in a batch, so one listing-heavy careers page can't eat the whole budget. On a real run this took batch coverage from 3 domains to 12.
- **Application tracker** — `output/applications.csv` gets a row per drafted application (date, company, role, status, fit score, CV path, cover-letter path, URL), keyed by job URL so re-drafting updates rather than duplicates. Marking a job applied/skipped in the UI updates its row.
- **Step-based dashboard flow** — the UI now shows exactly one "step" at a time instead of stacking panels on the page: Setup (role/preference chips, results hidden) → Running (progress + mini-game, results hidden) → Results (setup/progress hidden). A "Cancel" button in Setup backs out to Results without running anything.
- **Waiting mini-game** — while the pipeline runs, a canvas-based "dodge the red flags" game (🤖 jumps over 🚩, Space or tap) is shown below the step progress, with a `localStorage`-persisted high score. Purely cosmetic/entertainment — starts on run, stops and tears down its listeners/`requestAnimationFrame` loop on completion, error, or busy.
- **List/Grid view toggle** — job results can be viewed as a single-column list or a responsive card grid (1/2/3 columns); each card is a flex column with the action-button row pinned to the bottom (`mt-auto`) so buttons line up across a row regardless of how much match-reason/red-flag text a job has. Mode persists in `localStorage`.
- **Job source badge** — each card shows the posting's site (e.g. `glassdoor.co.in`, `wellfound.com`) derived client-side from `job.url`'s hostname, since `output/jobs.json` doesn't carry a `source` field (Claude's analyze step doesn't preserve it).
- **Headless mode** — `python agent.py` runs the same pipeline without the UI (auto-detects all roles, no preferences, unchanged behavior), printing progress to stdout.

---

## Workflows

**Full pipeline run (via dashboard)**
1. User clicks "Find Roles" → `analyzeResume()` calls `GET /api/resume-roles` → `renderSetup()` shows role checkboxes + preference chips, hides `#results-section` — `ui/index.html`
2. User adjusts roles/preferences, clicks "Start Search" → `startSearch()` builds the preferences string via `buildPreferences()`, hides setup, calls `runAgent(roles, skills, preferences)` — `ui/index.html`
3. `runAgent()` opens an SSE connection to `GET /api/run?roles=...&skills=...&preferences=...`, shows the progress section, starts the waiting game — `ui/index.html`
4. `server.py` acquires `run_lock`, starts pipeline thread with `resume_info={target_roles, key_skills}` and `preferences` — `server.py`
5. Step 1: `build_search_config(target_roles, key_skills, preferences)` writes `output/search_config.json` — `agent.py`
6. Step 2: `scrape_jobs()` searches + scrapes (Firecrawl → Exa fallback → snippet), writes `output/raw_jobs.json` — `agent.py`
7. Step 3: `analyze_jobs(preferences)` scores against resume + preferences, writes `output/jobs.json` — `agent.py`
8. Step 4: `generate_cover_letters()` writes one `.md` per apply-verdict job — `agent.py`
8b. Step 5: `generate_cvs()` writes + compiles + verifies one CV PDF per apply-verdict job — `agent.py`
9. On SSE `complete`/`error`/`busy`, `reset()` hides progress, stops the game, and re-shows `#results-section`; `complete` also calls `loadJobs()` → `GET /api/jobs` — `ui/index.html`

**Marking a job applied/skipped**
1. User clicks the (now full-width, bottom-pinned) status button on a job card — `ui/index.html` `toggleStatus()`
2. `POST /api/status` with `{url, status}` — `server.py`
3. Status persisted to `output/status.json`, next `/api/jobs` call merges it in
