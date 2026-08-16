# Routes & Server Actions

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-07-21
> Check here before adding a new route or action — no duplicates.

| Route | Method | Auth Required | What It Does |
|-------|--------|---------------|-------------|
| `/` | GET | No | Serves `ui/index.html` |
| `/api/jobs` | GET | No | Reads `output/jobs.json`, merges each job's applied/skipped status from `output/status.json`, returns list (empty list if no jobs file yet) |
| `/api/status` | POST | No | Body `{url, status}`, status ∈ `applied\|skipped\|none`. `none` removes the entry; others upsert into `output/status.json`. Also calls `set_application_status()`, which updates the matching `output/applications.csv` row if one exists (no-op otherwise) |
| `/api/cover-letter` | GET | No | Query params `company`, `title` → slugified filename lookup in `output/cover_letters/`; 404 if missing |
| `/api/cv` | GET | No | Query params `company`, `title` → same slug lookup in `output/cvs/`, returns the compiled PDF as `application/pdf`; 404 if missing |
| `/api/apply` | GET | No | Query param `url` → looks the job up in `output/jobs.json`, runs `apply_to_job()` on a background thread, streams SSE. Events: `{step: "Drafting"\|"Reviewing"\|"Revising"}`, then `{step: "complete", slug, draft, revised, review, skipped_edits}` or `{step: "error", message}`. 404 before any pipeline run or for an unknown URL. Not guarded by `run_lock` — it's per-job and independent of the pipeline |
| `/api/resume-roles` | GET | No | Runs `analyze_resume()` synchronously (single Claude call), returns `{target_roles, key_skills}`. 400 if `resume.md` missing, 500 (with the real error message) if the `claude` CLI call fails. Powers the dashboard's "Find Roles" step |
| `/api/run` | GET | No | Query params `roles` (repeated), `skills` (repeated), `preferences` (free text, optional) — all optional. Starts `run_pipeline(resume_info, preferences)` in a background thread (guarded by `run_lock`, one run at a time), streams progress as SSE. If `roles` is omitted, the pipeline auto-detects all roles via `analyze_resume()` (headless-compatible default). Returns `{step: "busy"}` immediately if already running |

## Pipeline steps (not HTTP routes, but the SSE step numbers `/api/run` reports)

1. Building search config — `build_search_config(target_roles, key_skills, preferences)` → `prompts/build_queries.md` (roles/skills come from a prior `analyze_resume()` call, either explicit via `/api/resume-roles` + UI selection, or auto-detected)
2. Scraping jobs — `scrape_jobs()` (Firecrawl search + scrape, Exa fallback for pages Firecrawl can't reach)
3. Analyzing & scoring — `analyze_jobs(preferences)` → `prompts/analyze.md`
4. Generating cover letters — `generate_cover_letters()` → `prompts/cover_letter.md`, only for jobs with score ≥ `THRESHOLD` (70) and `verdict == "apply"`
5. Generating CVs — `generate_cvs()` → `prompts/cv.md`, same job set as step 4. Writes `output/cvs/<slug>.typ`, compiles it with `typst` (`_compile_cv`), then checks the PDF's text layer with `pdftotext` (`_verify_cv`). Per-job failures are printed and skipped, never fatal

## Apply stage (not a pipeline step — triggered per job from the UI)

`GET /api/apply` → `apply_to_job(job)` in `agent.py`:

1. Restores the posting text via `_scraped_description()` (see `schema.md`) and archives it to `output/applications/<slug>/job_posting.md`
2. **Draft** — `prompts/apply_draft.md`, one `claude -p` call
3. **Review** — `prompts/apply_review.md`, a second call with fresh context, given the draft **inline** so it reviews exactly what was written. Returns ungrounded claims, requirement coverage, and structured edits
4. **Revise** — `_apply_edits()` applies the reviewer's `{old_string, new_string}` pairs in Python. An edit that doesn't match verbatim, or matches more than once, is skipped and surfaced in `skipped_edits` rather than guessed at

Two Claude calls, not three: the design sketched a third "revise" call, but the reviewer returns mechanical replacements, so Python applies them deterministically.
