# Systems

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-07-21

| System | Status | Details |
|--------|--------|---------|
| AI / LLM | Working | Claude Code CLI invoked as a subprocess (`run_claude()` in `agent.py`), not the Anthropic API/SDK directly. Prompts live as files in `prompts/`, `--allowedTools Read` only (no Write — Claude prints, Python writes files). Four call sites: resume analysis (`analyze_resume`), search-query building (`build_search_config`), job analysis/scoring, cover letter drafting. `run_claude()` wraps subprocess `OSError` (e.g. a broken/stub `claude` binary) into a `RuntimeError` so failures surface as a readable message instead of a raw crash — see [[history]]. |
| Search / Scrape | Working | Firecrawl (`firecrawl-py`) is primary: `app.search()` for discovery, `app.scrape()` with a JSON extraction schema for pulling individual postings off listing pages. Exa (`exa-py`, optional — `EXA_API_KEY`) is a fallback in `extract_postings()`/`_extract_via_exa()`: when Firecrawl's scrape fails or returns nothing (LinkedIn/Reddit reliably respond "Website Not Supported"), Exa's `get_contents()` with a schema-based `summary` option retries structured extraction on the same URL. Falls back further to the search snippet as a single posting if both fail. |
| Background Jobs | Working | `server.py`'s `/api/run` spins the pipeline on a `threading.Thread`, guarded by a single `threading.Lock` so concurrent runs are rejected with a `busy` SSE event. |
| Realtime | Working | Server-Sent Events (`StreamingResponse`) push pipeline step progress to the UI via a `queue.Queue` bridged into an async generator. |
| Auth | None | Local single-user tool, no auth anywhere. |
| Database | None | Flat JSON files under `output/` (gitignored) — see [[schema]]. |
| Storage | None | No file uploads; cover letters are just written to disk by Python. |
| Payments | None | |
| Email | None | |
