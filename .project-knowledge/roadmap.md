# Roadmap

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-08-16
> Forward-looking only. Check this before starting any task — know what's in flight.

## Current Goal

All five pipeline stages plus the apply stage have now run end to end on real scraped postings against the real resume (2026-08-16). Remaining work is quality, not completeness — see the TODOs.

---

## Known Bugs

- [x] ~~**The best-matching source can vanish between runs.**~~ Fixed 2026-08-16 by persisting every discovered page to `output/page_queue.json` and adding "Find more jobs", which works through the leftovers instead of discarding them. Original report: Discovery returns 73–168+ candidate pages but `MAX_PAGES_TO_SCRAPE = 20` caps scraping, and which 20 survive depends on search-result ordering that shifts run to run. Run 1 (2026-08-16) scraped 4 `community.n8n.io` postings including a real n8n hiring post that scores 88 for this resume — the single best match found all session. Run 2, same queries, scraped **zero** of them. The round-robin interleave spreads across queries but the Reddit/community queries sit last in the list, so their hits are the first cut. *(found: 2026-08-16)*
- [x] ~~**One employer can flood a run.**~~ Fixed 2026-08-16 with `MAX_PAGES_PER_DOMAIN = 3` in `_pick_batch()`. Original report: Run 2's 168 postings included 30 from `opentrain.ai` and 19 from `dynamitejobs.com` — a single career page yielding dozens of near-identical roles. Five of the ten `apply`-verdict jobs were OpenTrain. Nothing caps postings per company or per domain, so a listing-heavy site crowds out everything else downstream. *(found: 2026-08-16)*

- [ ] Local `claude` CLI install repeatedly reverts to a broken stub (native binary missing) — happened ~4x in one session on this machine (`/home/frieso/.npm-global/bin/claude`). Not a bug in this repo's code (`run_claude()` now at least surfaces it as a clear error instead of crashing), but the recurrence itself is unexplained — likely an auto-updater issue on the machine. Fix each time with `node <npm-global>/lib/node_modules/@anthropic-ai/claude-code/install.cjs`. *(found: 2026-07-21)*

---

## Active TODOs

- [ ] LinkedIn still yields nothing usable — Firecrawl returns "Website Not Supported" and the Exa fallback then failed to parse on one of four attempts (`Expecting value: line 1 column 1`). Worth deciding whether to keep spending discovery slots on `linkedin.com/jobs` at all. *(found in the 2026-08-16 real run)*
- [ ] Some scraped listing pages still yield thin descriptions (100 of 168 under 200 chars after the extract-prompt fix) — these are teaser cards on search/category pages, where the full text genuinely isn't on the page. Consider a second scrape pass on the individual posting URL for jobs that score near the threshold. *(added: 2026-08-16)*
- [ ] `posted_date` comes back as free text ("11 months ago", "3 weeks ago", "2 years ago") and is passed to `analyze.md` as-is for the 30-day freshness rule. It works, but nothing normalizes or verifies it. *(added: 2026-08-16)*
- [ ] Decide whether the apply stage should run in bulk during the pipeline instead of one job at a time from the UI — currently it's per-job and on demand, which is cheap but manual. *(added: 2026-08-16)*

---

## Planned Features

- [x] ~~**Drafter-reviewer apply stage**~~ — built 2026-08-16 (`apply_to_job()`, `prompts/apply_draft.md` + `apply_review.md`, `GET /api/apply`, side-by-side modal). Two Claude calls rather than three: the reviewer's edits are mechanical, so Python applies them. Original design: per-job flow on high-scoring `apply`-verdict jobs. Three new prompt files (`prompts/apply_draft.md`, `apply_review.md`, `apply_revise.md`) mirroring the strict raw-JSON contract. Draft via one `claude -p` subprocess, critique via a second fresh-context subprocess, revise via a third; drafts passed **inline** (never re-read) to save tokens. Reviewer returns structured edits `{old_string, new_string, reason}` the revise step applies mechanically. Includes a **factual grounding audit** (every claim traced to a `resume.md` line) and a **requirement-coverage check** (matched / gapped / bridged — honest gaps acknowledged, never stuffed). Wired as a new `POST /api/apply` SSE endpoint + Apply button on job cards with side-by-side initial-vs-revised viewer. *(designed: 2026-08-16)*
- [x] ~~**CV generation + PDF compile + ATS verification**~~ — built 2026-08-16 as pipeline step 5 (`generate_cvs()` + `prompts/cv.md` + `/api/cv`). Completed 2026-08-16: `_missing_keywords()` reports posting terms absent from the CV, and an over-one-page CV is regenerated once with instructions to cut the least relevant material. Original design: generate a per-job tailored CV from `resume.md` rendered through `templates/cv.typ`, compile with Typst, inspect the rendered PDF (page count, orphans, layout), then `pdftotext` ATS checks: email/phone as literal text, sane reading order, and a keyword-coverage table (covered / synonym-only / missing-have-it / missing-gap — never stuffed). Relevance-weighted cutting when a CV overflows the page limit. *(designed: 2026-08-16)*
- [x] ~~**Application tracker + posting archive**~~ — built 2026-08-16 (`record_application()`/`set_application_status()`, `output/applications/<slug>/job_posting.md`). Original design: `output/applications.csv` (`date, company, role, status, fit_score, cv_file, cover_letter_file, source`) replacing/augmenting the applied/skipped-only `output/status.json`, plus verbatim posting text archived to `output/applications/<company>_<role>/job_posting.md` (never reconstructed from memory). *(designed: 2026-08-16)*
- [x] ~~**Language gate**~~ — added to `prompts/analyze.md` 2026-08-16. Original design: a posting requiring a language absent from the resume hard-fails; a posting requiring a higher level than declared gets flagged (not silently dropped). *(designed: 2026-08-16)*
