# Stack

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-08-16

## Tech Stack

| Category | Details |
|----------|---------|
| Language | Python 3.10+ |
| Runtime | CPython, single process |
| Framework | FastAPI (server.py) + uvicorn |
| Database | None — flat JSON files in `output/` |
| ORM / Query | N/A |
| Auth | None (local-only tool) |
| Styling | Tailwind (CDN, no build step) |
| State Mgmt | Vanilla JS, in-memory (`allJobs` array in `ui/index.html`) |
| Testing | pytest + httpx (FastAPI TestClient) |
| Key Libraries | `firecrawl-py` (search + scrape), `exa-py` (fallback extraction), `python-dotenv` |
| AI | Claude Code CLI invoked as a subprocess (`claude -p ...`), not the Anthropic SDK |
| Deployment | None — local dev tool, run via `python server.py` |

## Dev Commands

| Command | What It Does |
|---------|-------------|
| `python -m venv .venv && .venv/bin/pip install -r requirements.txt` | Install deps (needed on externally-managed Python distros, e.g. Arch — plain `pip install` fails there) |
| `python server.py` | Start FastAPI dashboard at http://127.0.0.1:8000 |
| `python agent.py` | Run the 4-step pipeline headless (no UI) |
| `pytest` | Run `test_pipeline.py` + `test_server.py` (Claude/Firecrawl mocked) |

## Environment Variables

| Variable | Used In | What It Enables |
|----------|---------|----------------|
| `FIRECRAWL_API_KEY` | `agent.py` (`scrape_jobs`) | Firecrawl search + scrape calls |
| `EXA_API_KEY` | `agent.py` (`scrape_jobs`, `_extract_via_exa`) | Optional. Fallback structured extraction for pages Firecrawl can't scrape (LinkedIn, Reddit respond "Website Not Supported"). Pipeline works without it — falls straight to the search snippet instead |

## CV Toolchain (planned — for the apply stage, added 2026-08-16)

| Tool | Where | Purpose |
|------|-------|---------|
| `typst` (v0.15.1) | `~/.local/bin/typst` | Preferred CV compiler (decision pending user's render comparison — see roadmap) — single binary, ~0.27 s compiles, deterministic, clean ATS text layer |
| Portable TinyTeX (LaTeX) | `~/.TinyTeX/bin/x86_64-linux/lualatex` | Fallback CV compiler — needs `tlmgr` package installs (`fontawesome5`, `luatexbase`), ~0.8 s compiles, icon glyphs leak as noise into the ATS text layer |
| Font Awesome 5 OTFs | `~/.local/share/fonts` | Section icons in the CV (referenced by codepoint via `str.from-unicode()`, no built-in `icon()` in Typst 0.15) |
| `pdftotext` (poppler-utils) | PATH | ATS text-layer verification of compiled CVs (email/phone literal, reading order, keyword coverage) |

Demo CVs from the test-drive: `/tmp/opencode/cv-demo/`.

## External Prerequisites (not env vars)

- `claude` CLI must be installed and authenticated on PATH — `agent.py` shells out to it via `subprocess.run` in `run_claude()`. No Anthropic API key is used directly.
- `resume.md` in project root — gitignored, user-supplied, required for the pipeline to run at all (`run_pipeline` raises `RuntimeError` if missing).
