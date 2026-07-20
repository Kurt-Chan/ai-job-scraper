# AI Job Hunt Agent

[![Support me on Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20this%20project-FF5E5B?logo=ko-fi&logoColor=white)](https://ko-fi.com/kurtdeaustria)

An autonomous job-hunting pipeline. It reads your resume, searches the web for matching remote roles, scores each posting against your actual profile with Claude, and drafts a tailored cover letter for every job worth applying to — all reviewable in a local web dashboard.

It works for **any profession** — developer, designer, virtual assistant, writer, accountant, marketer. Everything (target roles, search queries, scoring, cover letters) is derived from your `resume.md`; nothing about your field is hardcoded.

## How it works

```
resume.md
   │
   ▼
1. Build search config   Claude extracts target roles, key skills, and
   │                     search queries from your resume
   ▼
2. Discover & scrape     Firecrawl runs the queries, then scrapes each
   │                     result page and extracts individual postings
   ▼
3. Analyze & score       Claude scores every posting 0–100 against your
   │                     profile (stack match, seniority, remote signals,
   │                     freshness, red flags) and gives a verdict
   ▼
4. Cover letters         For each "apply" verdict, Claude drafts a short
   │                     cover letter using a suggested angle per job
   ▼
output/jobs.json + output/cover_letters/*.md
```

A FastAPI server (`server.py`) exposes the pipeline and results, and `ui/index.html` is a single-file dashboard with live progress (Server-Sent Events), score/verdict filtering, applied/skipped tracking, and a cover-letter viewer.

## Stack

- **Python + FastAPI** — pipeline orchestration and API
- **[Firecrawl](https://firecrawl.dev)** — web search and structured scraping (LLM extraction with a JSON schema)
- **[Claude Code CLI](https://claude.com/claude-code)** — resume analysis, job scoring, and cover-letter writing via prompt files in `prompts/`
- **Vanilla JS + Tailwind** — zero-build single-file UI

## Setup

Requirements: Python 3.10+, the `claude` CLI installed and authenticated, and a Firecrawl API key.

```bash
pip install -r requirements.txt
cp .env.example .env        # add your FIRECRAWL_API_KEY
```

Then add your own `resume.md` in the project root (markdown resume — it is gitignored and never leaves your machine).

Optionally edit `config.json` to change where the agent searches: `job_boards` is the list of sites to query (one search each), and `reddit_groups` are groups of subreddits (one grouped search each, with optional `extra_terms` added to the query). The defaults cover LinkedIn, Indeed, Wellfound, Glassdoor, JobStreet, OnlineJobs.ph, and a set of profession-neutral hiring subreddits — if your field has dedicated boards or subreddits (e.g. Dribbble for designers, r/VirtualAssistant for VAs), add them here.

## Run

```bash
# Web dashboard
python server.py            # → http://127.0.0.1:8000

# Or headless
python agent.py
```

Results land in `output/` (gitignored): `jobs.json` (scored jobs), `raw_jobs.json` (everything scraped), and `cover_letters/`.

## Tests

```bash
pytest
```

## Project structure

```
agent.py          # 4-step pipeline (search config → scrape → analyze → cover letters)
config.json       # search sources: job boards + Reddit subreddit groups
server.py         # FastAPI: /api/jobs, /api/status, /api/cover-letter, /api/run (SSE)
ui/index.html     # single-file dashboard
prompts/          # Claude prompt files for each AI step
CLAUDE.md         # agent context (target roles, preferences, output contract)
test_pipeline.py  # pipeline unit tests (Claude/Firecrawl mocked)
test_server.py    # API tests
```

## Support

I built this while job hunting as a broke developer — it runs on a Claude Code subscription and Firecrawl's free tier precisely because I couldn't justify another bill. If it helped you land interviews (or saved you a few hours of job-board scrolling), consider buying me a coffee:

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/kurtdeaustria)

Stars, issues, and PRs are just as appreciated. ☕
