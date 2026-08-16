# Roadmap

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-08-16
> Forward-looking only. Check this before starting any task — know what's in flight.

## Current Goal

Implement the drafter-reviewer apply stage. CV generation (step 5) shipped 2026-08-16; the apply flow is still only designed.

---

## Known Bugs

- [ ] Local `claude` CLI install repeatedly reverts to a broken stub (native binary missing) — happened ~4x in one session on this machine (`/home/frieso/.npm-global/bin/claude`). Not a bug in this repo's code (`run_claude()` now at least surfaces it as a clear error instead of crashing), but the recurrence itself is unexplained — likely an auto-updater issue on the machine. Fix each time with `node <npm-global>/lib/node_modules/@anthropic-ai/claude-code/install.cjs`. *(found: 2026-07-21)*

---

## Active TODOs


---

## Planned Features

- [ ] **Drafter-reviewer apply stage** — per-job flow on high-scoring `apply`-verdict jobs. Three new prompt files (`prompts/apply_draft.md`, `apply_review.md`, `apply_revise.md`) mirroring the strict raw-JSON contract. Draft via one `claude -p` subprocess, critique via a second fresh-context subprocess, revise via a third; drafts passed **inline** (never re-read) to save tokens. Reviewer returns structured edits `{old_string, new_string, reason}` the revise step applies mechanically. Includes a **factual grounding audit** (every claim traced to a `resume.md` line) and a **requirement-coverage check** (matched / gapped / bridged — honest gaps acknowledged, never stuffed). Wired as a new `POST /api/apply` SSE endpoint + Apply button on job cards with side-by-side initial-vs-revised viewer. *(designed: 2026-08-16)*
- [x] ~~**CV generation + PDF compile + ATS verification**~~ — built 2026-08-16 as pipeline step 5 (`generate_cvs()` + `prompts/cv.md` + `/api/cv`). Shipped narrower than designed: no relevance-weighted cutting loop and no keyword-coverage table — the prompt handles trimming and vocabulary matching, and `_verify_cv()` only checks text-layer emptiness, a literal email, and page count. Those two remain open if wanted. Original design: generate a per-job tailored CV from `resume.md` rendered through `templates/cv.typ`, compile with Typst, inspect the rendered PDF (page count, orphans, layout), then `pdftotext` ATS checks: email/phone as literal text, sane reading order, and a keyword-coverage table (covered / synonym-only / missing-have-it / missing-gap — never stuffed). Relevance-weighted cutting when a CV overflows the page limit. *(designed: 2026-08-16)*
- [ ] **Application tracker + posting archive** — `output/applications.csv` (`date, company, role, status, fit_score, cv_file, cover_letter_file, source`) replacing/augmenting the applied/skipped-only `output/status.json`, plus verbatim posting text archived to `output/applications/<company>_<role>/job_posting.md` (never reconstructed from memory). *(designed: 2026-08-16)*
- [ ] **Language gate** in `prompts/analyze.md` — a posting requiring a language absent from the resume hard-fails; a posting requiring a higher level than declared gets flagged (not silently dropped). *(designed: 2026-08-16)*
