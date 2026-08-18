# AI Job Hunt Agent

[![Support me on Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20this%20project-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/kurtdeaustria)

An autonomous job-hunting pipeline. It reads your resume, searches the web for matching remote roles, scores each posting against your actual profile with Claude, then writes a tailored cover letter **and** a one-page PDF CV for every job worth applying to — all reviewable in a local web dashboard.

Before you send anything, a second Claude call reviews the letter with fresh context and flags any claim it can't trace back to a line in your resume. On a real run it caught "four years" where the resume said 2021–present, and "available full-time" where the current role was listed as part-time.

It works for **any profession** — developer, designer, virtual assistant, writer, accountant, marketer. Everything (target roles, search queries, scoring, cover letters) is derived from your `resume.md`; nothing about your field is hardcoded.

## How it works

```
resume.md
   │
   ▼
0. Find roles            Claude extracts target roles + key skills. The
   │                     dashboard lets you pick which roles to search and
   │                     set preferences (employment type, pay, location).
   ▼
1. Build search config   Claude turns the selected roles/skills/preferences
   │                     into search queries
   ▼
2. Discover & scrape     Firecrawl runs the queries, then scrapes a batch of
   │                     result pages and extracts individual postings. Pages
   │                     it didn't get to are queued, not discarded — "Find
   │                     more jobs" works through them without re-searching
   │                     or re-scraping anything
   ▼
3. Analyze & score       Claude scores every posting 0–100 against your
   │                     profile and preferences (stack match, seniority,
   │                     remote signals, freshness, red flags) and gives a verdict
   ▼
4. Cover letters         For each "apply" verdict, Claude drafts a short
   │                     cover letter using a suggested angle per job
   ▼
5. Tailored CVs          For the same jobs, Claude writes a Typst CV aimed at
   │                     that posting, compiles it to PDF, and checks the
   │                     text layer an ATS would read
   ▼
output/jobs.json + output/cover_letters/*.md + output/cvs/*.pdf
```

Then, per job, on demand from the dashboard:

```
Apply  →  draft  →  a second Claude call reviews it with fresh context,
                    flagging claims it can't find in your resume and
                    scoring requirement coverage
          ↓
          the reviewer's edits are applied, and the application is
          archived + tracked in output/applications.csv
```

A FastAPI server (`server.py`) exposes the pipeline and results. `ui/index.html` is a single-file dashboard with a step-based flow, live progress over Server-Sent Events, score/verdict filtering, applied/skipped tracking, a cover-letter viewer, a per-job CV download, an **Apply** button showing draft vs reviewed side by side, and a **Find more jobs** button.

## Dashboard

The dashboard walks through three steps instead of stacking everything on one page:

1. **Find Roles** — reads your resume and shows the derived target roles as checkboxes (uncheck any you don't want this run), plus preference chips for **employment type** (Full-time/Part-time/Contract/Freelance/Hourly), **pay/currency** (USD/EUR/GBP), and **location** — a "Worldwide Remote" chip or a text field for a specific country, mutually exclusive (checking one clears the other) so preferences never accidentally widen back to "worldwide or that country". A **Local currency** chip only becomes available once you type a country, and its value in the preferences string names that country explicitly (e.g. "Local currency (Egypt)") instead of leaving Claude to guess what "local" means. Preferences are folded into both the search queries and the scoring, so e.g. "Egypt, Part-time or Hourly work, paid in USD" actually steers results instead of defaulting to whatever a generic "remote" query happens to surface. Note: typing a country here searches *for* that country — there's no "exclude" option, so if you don't want a region's results, leave it blank or use "Worldwide Remote" rather than naming the region you're trying to avoid. Selections persist between runs. Hit **Cancel** to back out without running anything.
2. **Start Search** — runs the pipeline; while it's working there's a small "dodge the red flags" mini-game (🤖 jump over 🚩 with Space or a tap) to pass the time.
3. **Results** — job list with score/verdict filtering, a **List/Grid** view toggle, a source-site badge per job (e.g. `wellfound.com`), and applied/skipped status tracking. Each card carries **Cover Letter**, **CV ↗** (the compiled PDF), and **Apply**; a **Find more jobs** button sits above the list.

### Apply

Opens a modal and streams three phases — draft, review, revise — showing the initial draft and the reviewed version side by side, plus:

- **Claims not found in your resume**, with the reviewer's reasoning for each
- **Requirement coverage** per posting requirement: `matched` / `bridged` / `gap`. Gaps are expected and fine — the reviewer only objects when the letter *hides* one
- **Edits skipped**, if the reviewer's replacement text didn't match the draft exactly. Those are left alone rather than guessed at

Everything lands in `output/applications/<company>__<role>/` — the posting's own text, the draft, the review JSON, and the final letter — plus a row in `output/applications.csv`.

### Find more jobs

A search turns up far more pages than one run scrapes (46–168 in practice, 20 scraped). The rest aren't discarded: they're queued in `output/page_queue.json`, and this button scrapes the **next** batch. No repeated search, no page scraped twice, and cover letters or CVs already written are skipped — so a second look costs less than a second run.

No single site gets more than 3 pages per batch either, so one listing-heavy careers page can't eat the whole budget.

## Stack

- **Python + FastAPI** — pipeline orchestration and API
- **[Firecrawl](https://firecrawl.dev)** — web search and structured scraping (LLM extraction with a JSON schema)
- **[Exa](https://exa.ai)** *(optional)* — fallback structured extraction for pages Firecrawl can't scrape (e.g. LinkedIn, Reddit)
- **[Claude Code CLI](https://claude.com/claude-code)** — resume analysis, job scoring, cover letters, CV generation, and the apply reviewer, all via prompt files in `prompts/`
- **[Typst](https://github.com/typst/typst)** — CV typesetting; a single binary, sub-second compiles, and a clean text layer for ATS parsers
- **Vanilla JS + Tailwind** — zero-build single-file UI

## Setup

Requirements: Python 3.10+, the `claude` CLI installed and authenticated, and a Firecrawl API key. For CVs you also want [Typst](https://github.com/typst/typst) on your PATH, and optionally `pdftotext` (from poppler) for the ATS check — both are covered below.

```bash
pip install -r requirements.txt
cp .env.example .env        # add your FIRECRAWL_API_KEY (and optionally EXA_API_KEY)
```

> On distros with an externally-managed Python (e.g. Arch), use a virtualenv instead: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`, then run commands as `.venv/bin/python ...`.

Then add your own `resume.md` in the project root (markdown resume — it is gitignored and never leaves your machine).

Optionally edit `config.json` to change where the agent searches: `job_boards` is the list of sites to query (one search each), and `reddit_groups` are groups of subreddits (one grouped search each, with optional `extra_terms` added to the query). The defaults cover LinkedIn, Indeed, Wellfound, Glassdoor, RemoteOK, We Work Remotely, and a set of profession-neutral hiring subreddits — all globally remote-first, no region-specific boards baked in. If your field or region has dedicated boards or subreddits (e.g. Dribbble for designers, JobStreet/OnlineJobs.ph for Southeast Asia, r/VirtualAssistant for VAs), add them here. Note that `job_boards` are queried every run regardless of the dashboard's location preferences — a board tied to a specific region will keep surfacing results from that region no matter what you type in Search Setup, since the preferences only change the query wording, not which sites get searched.

## Run

```bash
# Web dashboard
python server.py            # → http://127.0.0.1:8000

# Or headless
python agent.py
```

Results land in `output/` (gitignored): `jobs.json` (scored jobs), `raw_jobs.json` (everything scraped), `cover_letters/`, `cvs/` (tailored `.typ` sources + compiled `.pdf`s), `applications/<company>__<role>/` (archived posting, draft, review, final letter), and `applications.csv` (the tracker).

### CV toolchain

Step 5 shells out to `typst`, so it needs to be on your PATH. It's a single self-contained binary — grab a release from [typst/typst](https://github.com/typst/typst/releases) and drop it in `~/.local/bin`, or use your package manager (`brew install typst`, `pacman -S typst`, `winget install Typst.Typst`, `cargo install --locked typst-cli`).

`pdftotext` (from poppler-utils, likely already installed) is optional — with it, every compiled CV is read back the way an ATS would read it and warns about an empty text layer, a missing email, a second page, or terms the posting asks for that your resume supports but the CV left out. A CV that overflows one page is regenerated once, told to cut the least relevant material.

Neither tool is required to run the rest: a missing `typst` fails only step 5 and only per job, and a missing `pdftotext` just skips verification.

`templates/cv.typ` is the styling reference every generated CV follows — edit it to change fonts, spacing, or section layout. Render it standalone to preview changes:

```bash
typst compile templates/cv.typ
```

## Tests

```bash
pytest
```

## Project structure

```
agent.py          # pipeline: roles → queries → scrape → score → letters → CVs, plus the apply stage
config.json       # search sources: job boards + Reddit subreddit groups
server.py         # FastAPI: /api/jobs, /api/status, /api/cover-letter, /api/cv,
                  #          /api/apply (SSE), /api/resume-roles, /api/run (SSE)
ui/index.html     # single-file dashboard (step flow, chips, list/grid, apply modal, mini-game)
prompts/          # Claude prompt files — one per AI step, including cv.md and the apply pair
templates/cv.typ  # Typst CV layout every generated CV is styled after
CLAUDE.md         # agent context (target roles, preferences, output contract)
test_pipeline.py  # pipeline unit tests (Claude/Firecrawl/Exa/typst/pdftotext mocked)
test_server.py    # API tests
```

## Support

I built this while job hunting as a broke developer — it runs on a Claude Code subscription and Firecrawl's free tier precisely because I couldn't justify another bill. If it helped you land interviews (or saved you a few hours of job-board scrolling), consider buying me a coffee:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kurtdeaustria)

Stars, issues, and PRs are just as appreciated. ☕

---

> Part of this repo's living knowledge — a `.project-knowledge/` folder tracks the stack, architecture, schema, features, roadmap, and session history. It's kept in sync as the project evolves, so the docs never go stale. 🧠
