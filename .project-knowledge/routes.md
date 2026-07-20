# Routes & Server Actions

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-07-21
> Check here before adding a new route or action — no duplicates.

| Route | Method | Auth Required | What It Does |
|-------|--------|---------------|-------------|
| `/` | GET | No | Serves `ui/index.html` |
| `/api/jobs` | GET | No | Reads `output/jobs.json`, merges each job's applied/skipped status from `output/status.json`, returns list (empty list if no jobs file yet) |
| `/api/status` | POST | No | Body `{url, status}`, status ∈ `applied\|skipped\|none`. `none` removes the entry; others upsert into `output/status.json` |
| `/api/cover-letter` | GET | No | Query params `company`, `title` → slugified filename lookup in `output/cover_letters/`; 404 if missing |
| `/api/resume-roles` | GET | No | Runs `analyze_resume()` synchronously (single Claude call), returns `{target_roles, key_skills}`. 400 if `resume.md` missing, 500 (with the real error message) if the `claude` CLI call fails. Powers the dashboard's "Find Roles" step |
| `/api/run` | GET | No | Query params `roles` (repeated), `skills` (repeated), `preferences` (free text, optional) — all optional. Starts `run_pipeline(resume_info, preferences)` in a background thread (guarded by `run_lock`, one run at a time), streams progress as SSE. If `roles` is omitted, the pipeline auto-detects all roles via `analyze_resume()` (headless-compatible default). Returns `{step: "busy"}` immediately if already running |

## Pipeline steps (not HTTP routes, but the SSE step numbers `/api/run` reports)

1. Building search config — `build_search_config(target_roles, key_skills, preferences)` → `prompts/build_queries.md` (roles/skills come from a prior `analyze_resume()` call, either explicit via `/api/resume-roles` + UI selection, or auto-detected)
2. Scraping jobs — `scrape_jobs()` (Firecrawl search + scrape, Exa fallback for pages Firecrawl can't reach)
3. Analyzing & scoring — `analyze_jobs(preferences)` → `prompts/analyze.md`
4. Generating cover letters — `generate_cover_letters()` → `prompts/cover_letter.md`, only for jobs with score ≥ `THRESHOLD` (70) and `verdict == "apply"`
