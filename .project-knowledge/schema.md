# Schema

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-07-21
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

## `output/status.json`

Simple map, written/read by `server.py` (`_read_status` / `_write_status`).

```json
{ "<job url>": "applied | skipped" }
```

Entries are removed (not set to `"none"`) when status is cleared.

## `output/cover_letters/*.md`

One plain-text file per "apply"-verdict job, named `{slug(company)}__{slug(title)}.md` (see `_slug()` in `agent.py`). No frontmatter — raw cover letter text only.
