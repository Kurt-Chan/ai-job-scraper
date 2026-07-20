# History

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-07-21
> Past-only. Append-only — never delete entries.

## Removed

_None recorded yet._

---

## Fixed

- LinkedIn/Reddit postings only ever got a bare search-snippet fallback (title/description only, no company/location) because Firecrawl returns "Website Not Supported" for those domains → added an Exa fallback in `extract_postings()` that retries structured extraction on the same URL before giving up to the snippet. *(fixed: 2026-07-20)*
- `analyzeResume()` in the UI showed `"Unexpected token 'I', \"Internal S\"... is not valid JSON"` on failure instead of a readable error → root cause was `agent.run_claude()` not catching `OSError` from a broken/stub `claude` binary, so it propagated as an unhandled exception and `server.py` returned a plain-text 500 instead of the expected `{detail: ...}` JSON. Fixed by wrapping the `subprocess.run` call in `run_claude()` with `try/except OSError` → `RuntimeError` with an actionable message. *(fixed: 2026-07-21)*
- Dashboard defaulted to searching every resume-derived role with no location/pay/employment-type targeting, which combined with India-heavy indexing on Indeed/Glassdoor/JobStreet for the AI/n8n query terms used in testing → results skewed toward `.co.in`/`in.indeed.com` full-time listings. Fixed by adding role selection + a preferences string (chips: employment type, currency, location) folded into both `build_queries.md` and `analyze.md`. *(fixed: 2026-07-21)*
- Grid-view job cards had their action buttons at inconsistent heights across a row (extra stretched space appeared *below* the buttons instead of the buttons sitting at the card's bottom edge) → made each card a flex column with the button area `mt-auto`. The "Mark Status" button also floated alone on a wrapped line due to `flex-wrap` + `ml-auto` in narrow cards → made it a deliberate full-width row below Open Job/Cover Letter instead of relying on wrap behavior. *(fixed: 2026-07-21)*

---

## Decisions

> Architectural and design decisions — the why behind the code.

- Claude is invoked via the `claude` CLI as a subprocess, not the Anthropic API/SDK directly — keeps the tool running on a Claude Code subscription instead of requiring a separate API key (per README "Support" section). *(observed 2026-07-20, predates this log)*
- Claude prompt calls only get `--allowedTools Read`, never `Write` — forces Claude to print results to stdout so Python remains the sole writer of `output/*.json`, keeping file-write behavior deterministic and testable. *(observed 2026-07-20, predates this log)*
- No database — all pipeline state is flat JSON in gitignored `output/`, since this is a single-user local tool with no need for concurrent multi-user storage. *(observed 2026-07-20, predates this log)*
- Exa is a fallback, not a Firecrawl replacement — scoped deliberately narrow (only retried when Firecrawl's scrape fails/returns nothing) rather than replacing Firecrawl's search or scrape wholesale, since Firecrawl already works for the majority of sites and Exa costs an extra API call. *(2026-07-20)*
- Resume analysis was split into two Claude calls (`analyze_resume()` → roles/skills only, then `build_search_config()` → queries) instead of one combined call, specifically so the UI can show roles for selection between the two steps. Costs one extra Claude subprocess call per run in exchange for that interactivity. *(2026-07-21)*
- Run preferences (location/pay/employment type) are a free-text string built from UI chip selections, not a rigid backend schema — chosen over fixed dropdowns (e.g. a hardcoded country list) because countries/pay rates are too open-ended to enumerate for a profession-agnostic tool; employment type *is* a small fixed set, so that one got dedicated chips (Full-time/Part-time/Contract/Freelance/Hourly). The string is passed as-is into `build_queries.md`/`analyze.md`, which already handle natural-language preferences. *(2026-07-21)*
- The waiting mini-game is pure front-end entertainment with no backend involvement — starts/stops tied directly to the progress-section visibility (`runAgent()`/`reset()`), so it never runs when not visible and never blocks or slows the actual pipeline. *(2026-07-21)*
