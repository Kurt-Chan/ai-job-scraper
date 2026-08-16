# AI Job Hunt Agent — Knowledge Index

> Last updated: 2026-08-16
> Status: Active
> Stack: Python + FastAPI + Firecrawl + Exa (fallback) + Claude Code CLI (subprocess) + vanilla JS/Tailwind
> Current goal: Implement the drafter-reviewer apply stage + per-job CV generation (PDF compile + ATS verification) designed on 2026-08-16 — see roadmap.md

## What This Project Does
An autonomous, profession-agnostic job-hunting pipeline. It reads a user-supplied `resume.md`, derives search queries with Claude, discovers and scrapes remote job postings via Firecrawl, scores each against the resume, and drafts cover letters for the best matches — all reviewable in a local single-file web dashboard.

---

## Files in This Folder

| File | Contents | Load when... |
|------|----------|--------------|
| `stack.md` | Tech stack, dev commands, env vars, external prerequisites | Setting up, adding deps, checking env vars |
| `structure.md` | File tree, entry points, key files | Navigating the codebase, adding new files |
| `schema.md` | Shape of every `output/*.json` file (no real DB) | Touching pipeline output or `/api/*` data |
| `routes.md` | FastAPI routes + pipeline SSE steps | Adding/changing endpoints or pipeline stages |
| `systems.md` | AI/LLM, search/scrape, background jobs, realtime (SSE) | Touching any cross-cutting system |
| `features.md` | User-facing features and workflows | Understanding what's built, adding features |
| `roadmap.md` | Bugs, TODOs, planned features, current goal | Starting any task — know what's in flight |
| `history.md` | Removed items, fixes, architectural decisions | Debugging, reviewing past decisions |
| `sessions.md` | Session-by-session log | Reviewing work history |

> Only files that exist are listed here. No `hooks.md`/`components.md` (no component framework — single HTML file) or `integrations.md` (no external systems read/write this project's data).

---

## Context Loading Guide

| Task | Load these files |
|------|-----------------|
| Adding/changing a FastAPI route | `routes.md` + `schema.md` |
| Changing pipeline logic (agent.py) | `structure.md` + `schema.md` + `systems.md` |
| Editing the dashboard UI | `features.md` + `routes.md` (it's one file: `ui/index.html`) |
| Changing prompt files | `systems.md` (AI/LLM row) + `schema.md` (output shapes the prompts must produce) |
| Fixing a bug | `roadmap.md` + file relevant to the bug area |
| Understanding a feature or flow | `features.md` + `routes.md` |
| General orientation (new session) | This file → then pick by task |
| Full audit | All files |
