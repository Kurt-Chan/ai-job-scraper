# AI Job Hunt Agent

[![Support me on Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20this%20project-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/kurtdeaustria)

An autonomous job-hunting pipeline. It reads your resume, searches the web for matching remote roles, scores each posting against your actual profile with Claude, and drafts a tailored cover letter for every job worth applying to — all reviewable in a local web dashboard.

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
2. Discover & scrape     Firecrawl runs the queries, then scrapes each
   │                     result page and extracts individual postings
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

A FastAPI server (`server.py`) exposes the pipeline and results, and `ui/index.html` is a single-file dashboard with a step-based flow, live progress (Server-Sent Events), score/verdict filtering, applied/skipped tracking, and a cover-letter viewer, and a per-job CV download.

## Dashboard

The dashboard walks through three steps instead of stacking everything on one page:

1. **Find Roles** — reads your resume and shows the derived target roles as checkboxes (uncheck any you don't want this run), plus preference chips for **employment type** (Full-time/Part-time/Contract/Freelance/Hourly), **pay/currency** (USD/EUR/GBP), and **location** — a "Worldwide Remote" chip or a text field for a specific country, mutually exclusive (checking one clears the other) so preferences never accidentally widen back to "worldwide or that country". A **Local currency** chip only becomes available once you type a country, and its value in the preferences string names that country explicitly (e.g. "Local currency (Egypt)") instead of leaving Claude to guess what "local" means. Preferences are folded into both the search queries and the scoring, so e.g. "Egypt, Part-time or Hourly work, paid in USD" actually steers results instead of defaulting to whatever a generic "remote" query happens to surface. Note: typing a country here searches *for* that country — there's no "exclude" option, so if you don't want a region's results, leave it blank or use "Worldwide Remote" rather than naming the region you're trying to avoid. Selections persist between runs. Hit **Cancel** to back out without running anything.
2. **Start Search** — runs the pipeline; while it's working there's a small "dodge the red flags" mini-game (🤖 jump over 🚩 with Space or a tap) to pass the time.
3. **Results** — job list with score/verdict filtering, a **List/Grid** view toggle, a source-site badge per job (e.g. `wellfound.com`), and applied/skipped status tracking.

## Stack

- **Python + FastAPI** — pipeline orchestration and API
- **[Firecrawl](https://firecrawl.dev)** — web search and structured scraping (LLM extraction with a JSON schema)
- **[Exa](https://exa.ai)** *(optional)* — fallback structured extraction for pages Firecrawl can't scrape (e.g. LinkedIn, Reddit)
- **[Claude Code CLI](https://claude.com/claude-code)** — resume analysis, job scoring, and cover-letter writing via prompt files in `prompts/`
- **Vanilla JS + Tailwind** — zero-build single-file UI

## Setup

Requirements: Python 3.10+, the `claude` CLI installed and authenticated, and a Firecrawl API key.

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

Results land in `output/` (gitignored): `jobs.json` (scored jobs), `raw_jobs.json` (everything scraped), `cover_letters/`, and `cvs/` (tailored `.typ` sources + compiled `.pdf`s).

CV generation needs [Typst](https://github.com/typst/typst) on your PATH; `pdftotext` (poppler) is optional and enables the ATS text-layer check. Without Typst the other four steps still run — step 5 just reports the failure per job.

## Tests

```bash
pytest
```

## Project structure

```
agent.py          # pipeline: find roles → build queries → scrape → analyze → cover letters
config.json       # search sources: job boards + Reddit subreddit groups
server.py         # FastAPI: /api/jobs, /api/status, /api/cover-letter, /api/resume-roles, /api/run (SSE)
ui/index.html     # single-file dashboard (step flow, chips, list/grid view, mini-game)
prompts/          # Claude prompt files for each AI step
CLAUDE.md         # agent context (target roles, preferences, output contract)
test_pipeline.py  # pipeline unit tests (Claude/Firecrawl/Exa mocked)
test_server.py    # API tests
```

## Support

I built this while job hunting as a broke developer — it runs on a Claude Code subscription and Firecrawl's free tier precisely because I couldn't justify another bill. If it helped you land interviews (or saved you a few hours of job-board scrolling), consider buying me a coffee:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kurtdeaustria)

Stars, issues, and PRs are just as appreciated. ☕

---

> Part of this repo's living knowledge — a `.project-knowledge/` folder tracks the stack, architecture, schema, features, roadmap, and session history. It's kept in sync as the project evolves, so the docs never go stale. 🧠
