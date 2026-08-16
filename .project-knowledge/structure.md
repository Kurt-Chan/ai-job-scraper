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
│   ├── cover_letter.md         # step 4: one job JSON → plain-text cover letter
│   ├── cv.md                   # step 5: one job JSON + resume.md + template → Typst CV source
│   ├── apply_draft.md          # apply stage: job JSON + resume.md → cover letter draft
│   └── apply_review.md         # apply stage: job JSON + draft (inline) → {ungrounded_claims, coverage, edits}
├── templates/
│   └── cv.typ                 # Typst CV template — styling reference for prompts/cv.md
├── ui/
│   └── index.html               # single-file dashboard (vanilla JS + Tailwind CDN, no build step)
├── test_pipeline.py             # unit tests for agent.py (Claude/Firecrawl/Exa mocked)
├── test_server.py               # API tests for server.py (FastAPI TestClient)
└── output/                      # gitignored, generated at runtime
    ├── search_config.json
    ├── raw_jobs.json
    ├── jobs.json
    ├── status.json               # url → applied/skipped map
    ├── cover_letters/*.md
    ├── cvs/*.typ + *.pdf
    ├── applications.csv          # tracker, one row per drafted application
    └── applications/<slug>/      # job_posting.md, cover_letter_draft.md, review.json, cover_letter.md
```

## Key Files

| File | Purpose |
|------|---------|
| `agent.py` | All pipeline logic: config loading, URL dedup/canonicalization, Firecrawl search+scrape with Exa fallback (`_extract_via_exa`, `_normalize_postings`), Claude subprocess runner (`run_claude` — wraps `OSError` into `RuntimeError`), JSON parsing with fence-stripping, `analyze_resume()`/`build_search_config()` (role selection split from query building), cover letter generation, CV generation + Typst compile + ATS text-layer check (`generate_cvs`/`_compile_cv`/`_verify_cv`/`_missing_keywords`), the drafter-reviewer apply stage (`apply_to_job`/`_apply_edits`) and its tracker (`record_application`/`set_application_status`), `run_pipeline()` orchestrator used by both CLI and server |
| `server.py` | Thin FastAPI wrapper around `agent.py` — serves the UI, exposes job/status/cover-letter/CV-PDF/resume-role data, streams the per-job apply stage, streams pipeline progress via SSE using a background thread + queue |
| `ui/index.html` | Entire frontend in one file: step-based flow (setup → running → results), role/preference chip pickers, job list with score/verdict filtering + list/grid view, applied/skipped toggle, cover letter modal, CV download link, apply modal (draft vs reviewed, side by side), waiting mini-game |
| `templates/cv.typ` | Typst CV layout — sample content, real styling; read by `prompts/cv.md` as the style reference for every generated CV. Compile standalone with `typst compile templates/cv.typ`. Spacing rules that matter are documented in `history.md` (inline `line()` and tight-list gotchas) |
| `config.json` | User-editable search source list, same shape as `DEFAULT_CONFIG` in `agent.py`, merged via `load_config()` |
