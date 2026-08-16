# Schema

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-08-16
> No database — all state lives in gitignored JSON files under `output/`. This is a navigable summary of their shapes.

## `output/search_config.json`

Written by `build_search_config(target_roles, key_skills, preferences)` in `agent.py`. `search_queries` comes from `prompts/build_queries.md`; `target_roles`/`key_skills` are merged in afterward (they're the caller's selection/output of `analyze_resume()`, not re-derived by this prompt call).

```json
{
  "target_roles": ["string", "..."],
  "key_skills": ["string", "..."],
  "search_queries": ["string", "..."]
}
```

## `analyze_resume()` return shape (not persisted to a file, but returned by `GET /api/resume-roles`)

```json
{
  "target_roles": ["string", "..."],
  "key_skills": ["string", "..."]
}
```

## `output/raw_jobs.json`

Written by `run_pipeline()` after `scrape_jobs()`. Array of postings, deduped by canonical URL.

```json
[{
  "title": "string",
  "company": "string",
  "location": "string (defaults to 'Remote')",
  "url": "string",
  "description": "string",
  "posted_date": "string",
  "source": "string — canonical host, e.g. 'linkedin.com'"
}]
```

## `output/page_queue.json`

Every page the last search discovered, plus which of them have been scraped. Written by `scrape_jobs()`, advanced by `scrape_more()`.

```json
{
  "pages": [{"url": "string", "title": "string", "description": "string"}],
  "scraped": ["<_dedup_key(url)>", "..."]
}
```

Searching is cheap and scraping isn't, so discovery keeps everything it finds and only a batch of `MAX_PAGES_TO_SCRAPE` is paid for at a time. "Find more jobs" scrapes the next batch from `pages`, skipping anything already in `scraped`. A new search overwrites the file.

## `output/jobs.json`

Written by `analyze_jobs()`, produced by `prompts/analyze.md`. Only jobs scored ≥ 60 are included.

```json
[{
  "title": "string",
  "company": "string",
  "url": "string",
  "score": "number 0-100",
  "verdict": "apply | review | skip",
  "match_reasons": ["string"],
  "red_flags": ["string"],
  "suggested_angle": "string"
}]
```

`/api/jobs` adds a `status` field at read time (not persisted here) from `output/status.json`.

**Note the missing `description`** — `prompts/analyze.md` doesn't carry the posting text through, so anything that needs the posting's own words (CV tailoring, the apply stage's coverage review, the archived `job_posting.md`) reads it back from `output/raw_jobs.json` via `_scraped_description(url)`, matched on canonical URL. Never let Claude recall what a posting said.

## `output/status.json`

Simple map, written/read by `server.py` (`_read_status` / `_write_status`).

```json
{ "<job url>": "applied | skipped" }
```

Entries are removed (not set to `"none"`) when status is cleared.

## `output/cover_letters/*.md`

One plain-text file per "apply"-verdict job, named `{slug(company)}__{slug(title)}.md` (see `_slug()` in `agent.py`). No frontmatter — raw cover letter text only.

## `output/cvs/*.typ` + `*.pdf`

One tailored CV per "apply"-verdict job, same `{slug(company)}__{slug(title)}` naming. The `.typ` is Claude's generated Typst source (whole document, not a filled template); the `.pdf` is what `typst compile` produced from it. `GET /api/cv` serves the PDF.

## `output/applications.csv`

The application tracker, written by `record_application()` / `set_application_status()` in `agent.py`. Keyed by `source` (the job URL) — re-drafting the same job rewrites its row rather than appending a duplicate. Rewritten whole on every change, header included.

| Column | Notes |
|--------|-------|
| `date` | `YYYY-MM-DD`, the day the application was last drafted |
| `company`, `role` | Copied from the job |
| `status` | `drafted` on first write; `applied`/`skipped` when the UI's status button fires `POST /api/status` |
| `fit_score` | The job's `score` from `jobs.json` |
| `cv_file`, `cover_letter_file` | Repo-relative paths; `cv_file` is empty when no CV was generated |
| `source` | Job URL — the row key |

`POST /api/status` only updates rows that already exist. Marking a never-drafted job applied does **not** create a tracker row: the CSV records applications, not every job that was scored.

## `output/applications/<slug>/`

One directory per drafted application:

| File | Contents |
|------|----------|
| `job_posting.md` | The posting's title, URL and verbatim text, archived at draft time |
| `cover_letter_draft.md` | The drafter's output, before review |
| `review.json` | `{ungrounded_claims: [{claim, why}], coverage: [{requirement, status, note}], edits: [{old_string, new_string, reason}]}` — status is `matched \| bridged \| gap` |
| `cover_letter.md` | The draft with the reviewer's edits applied — the one to send |
