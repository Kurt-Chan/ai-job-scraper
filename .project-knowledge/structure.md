# Project Structure

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-07-21

## File Tree

```
.
├── agent.py              # pipeline: analyze resume → build queries → scrape → analyze → cover letters
├── server.py              # FastAPI app: /api/jobs, /api/status, /api/cover-letter, /api/resume-roles, /api/run (SSE)
├── config.json             # search sources: job_boards + reddit_groups (overrides agent.py defaults)
├── CLAUDE.md               # agent context for Claude Code (target roles, output contract)
├── README.md
├── LICENSE
├── requirements.txt
├── .env.example             # FIRECRAWL_API_KEY + optional EXA_API_KEY placeholders
├── .gitignore
├── resume.md                # gitignored, user-supplied, NOT in repo — required at runtime
├── .venv/                   # gitignored local virtualenv (Arch's Python is externally-managed)
├── prompts/
│   ├── analyze_resume.md     # step 0: resume.md → {target_roles, key_skills}
│   ├── build_queries.md      # step 1: selected roles/skills/preferences → {search_queries}
│   ├── analyze.md             # step 3: raw_jobs.json + resume.md + preferences → scored jobs.json
│   └── cover_letter.md         # step 4: one job JSON → plain-text cover letter
├── ui/
│   └── index.html               # single-file dashboard (vanilla JS + Tailwind CDN, no build step)
├── test_pipeline.py             # unit tests for agent.py (Claude/Firecrawl/Exa mocked)
├── test_server.py               # API tests for server.py (FastAPI TestClient)
└── output/                      # gitignored, generated at runtime
    ├── search_config.json
    ├── raw_jobs.json
    ├── jobs.json
    ├── status.json               # url → applied/skipped map
    └── cover_letters/*.md
```

## Key Files

| File | Purpose |
|------|---------|
| `agent.py` | All pipeline logic: config loading, URL dedup/canonicalization, Firecrawl search+scrape with Exa fallback (`_extract_via_exa`, `_normalize_postings`), Claude subprocess runner (`run_claude` — wraps `OSError` into `RuntimeError`), JSON parsing with fence-stripping, `analyze_resume()`/`build_search_config()` (role selection split from query building), cover letter generation, `run_pipeline()` orchestrator used by both CLI and server |
| `server.py` | Thin FastAPI wrapper around `agent.py` — serves the UI, exposes job/status/cover-letter/resume-role data, streams pipeline progress via SSE using a background thread + queue |
| `ui/index.html` | Entire frontend in one file: step-based flow (setup → running → results), role/preference chip pickers, job list with score/verdict filtering + list/grid view, applied/skipped toggle, cover letter modal, waiting mini-game |
| `config.json` | User-editable search source list, same shape as `DEFAULT_CONFIG` in `agent.py`, merged via `load_config()` |
