# Roadmap

> Part of ai-job-scraper-clean/.project-knowledge/ | Last updated: 2026-07-21
> Forward-looking only. Check this before starting any task — know what's in flight.

## Current Goal

Push the current state (Exa fallback, role/preference selection UI, waiting game, README + project-knowledge updates) to https://github.com/YahyaZekry/ai-job-scraper (existing repo, default branch `clean`).

---

## Known Bugs

- [ ] Local `claude` CLI install repeatedly reverts to a broken stub (native binary missing) — happened ~4x in one session on this machine (`/home/frieso/.npm-global/bin/claude`). Not a bug in this repo's code (`run_claude()` now at least surfaces it as a clear error instead of crashing), but the recurrence itself is unexplained — likely an auto-updater issue on the machine. Fix each time with `node <npm-global>/lib/node_modules/@anthropic-ai/claude-code/install.cjs`. *(found: 2026-07-21)*

---

## Active TODOs

_None recorded yet._

---

## Planned Features

_None recorded yet._
