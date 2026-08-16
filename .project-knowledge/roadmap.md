# Roadmap

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-08-16
> Forward-looking only. Check this before starting any task — know what's in flight.

## Current Goal

Everything on the 2026-08-16 design is built. Next: a real end-to-end run against the user's own `resume.md` and live Firecrawl results — every stage so far has been exercised against synthetic fixtures only.

---

## Known Bugs

- [ ] Local `claude` CLI install repeatedly reverts to a broken stub (native binary missing) — happened ~4x in one session on this machine (`/home/frieso/.npm-global/bin/claude`). Not a bug in this repo's code (`run_claude()` now at least surfaces it as a clear error instead of crashing), but the recurrence itself is unexplained — likely an auto-updater issue on the machine. Fix each time with `node <npm-global>/lib/node_modules/@anthropic-ai/claude-code/install.cjs`. *(found: 2026-07-21)*

---

## Active TODOs

- [ ] Run the whole pipeline end to end against the real `resume.md` + live Firecrawl/Exa results. Every stage has been verified against synthetic fixtures; none has been run on real scraped postings since the apply/CV work landed. *(added: 2026-08-16)*
- [ ] Decide whether the apply stage should run in bulk during the pipeline instead of one job at a time from the UI — currently it's per-job and on demand, which is cheap but manual. *(added: 2026-08-16)*

---

## Planned Features

- [x] ~~**Drafter-reviewer apply stage**~~ — built 2026-08-16 (`apply_to_job()`, `prompts/apply_draft.md` + `apply_review.md`, `GET /api/apply`, side-by-side modal). Two Claude calls rather than three: the reviewer's edits are mechanical, so Python applies them. Original design: per-job flow on high-scoring `apply`-verdict jobs. Three new prompt files (`prompts/apply_draft.md`, `apply_review.md`, `apply_revise.md`) mirroring the strict raw-JSON contract. Draft via one `claude -p` subprocess, critique via a second fresh-context subprocess, revise via a third; drafts passed **inline** (never re-read) to save tokens. Reviewer returns structured edits `{old_string, new_string, reason}` the revise step applies mechanically. Includes a **factual grounding audit** (every claim traced to a `resume.md` line) and a **requirement-coverage check** (matched / gapped / bridged — honest gaps acknowledged, never stuffed). Wired as a new `POST /api/apply` SSE endpoint + Apply button on job cards with side-by-side initial-vs-revised viewer. *(designed: 2026-08-16)*
- [x] ~~**CV generation + PDF compile + ATS verification**~~ — built 2026-08-16 as pipeline step 5 (`generate_cvs()` + `prompts/cv.md` + `/api/cv`). Completed 2026-08-16: `_missing_keywords()` reports posting terms absent from the CV, and an over-one-page CV is regenerated once with instructions to cut the least relevant material. Original design: generate a per-job tailored CV from `resume.md` rendered through `templates/cv.typ`, compile with Typst, inspect the rendered PDF (page count, orphans, layout), then `pdftotext` ATS checks: email/phone as literal text, sane reading order, and a keyword-coverage table (covered / synonym-only / missing-have-it / missing-gap — never stuffed). Relevance-weighted cutting when a CV overflows the page limit. *(designed: 2026-08-16)*
- [x] ~~**Application tracker + posting archive**~~ — built 2026-08-16 (`record_application()`/`set_application_status()`, `output/applications/<slug>/job_posting.md`). Original design: `output/applications.csv` (`date, company, role, status, fit_score, cv_file, cover_letter_file, source`) replacing/augmenting the applied/skipped-only `output/status.json`, plus verbatim posting text archived to `output/applications/<company>_<role>/job_posting.md` (never reconstructed from memory). *(designed: 2026-08-16)*
- [x] ~~**Language gate**~~ — added to `prompts/analyze.md` 2026-08-16. Original design: a posting requiring a language absent from the resume hard-fails; a posting requiring a higher level than declared gets flagged (not silently dropped). *(designed: 2026-08-16)*
