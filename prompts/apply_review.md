Read resume.md. You are reviewing a cover letter someone else drafted for the job below. You did not write it and have no stake in it — your job is to catch what's wrong with it.

The job JSON and the draft follow at the end of this prompt.

Check three things:

1. **Grounding.** Take every factual claim the letter makes — employer, title, tool, metric, duration, outcome — and find it in resume.md. A claim that isn't in the resume is ungrounded, even if it sounds plausible or is a reasonable inference. Inflated numbers, invented job titles, and "led" where the resume says "contributed to" all count as ungrounded.
2. **Requirement coverage.** For each requirement the posting states, decide: `matched` (the letter shows real evidence from the resume), `bridged` (the resume has adjacent experience the letter uses honestly), or `gap` (the candidate doesn't have it). Gaps are expected and fine — flag only when the letter *hides* a gap or implies coverage that isn't there.
3. **Edits.** Concrete text replacements that fix the problems above, or that cut waffle and vague filler. Each `old_string` must be copied **exactly** from the draft, long enough to appear only once. Set `new_string` to `""` to delete. Don't rewrite the whole letter — if it's fundamentally sound, return few edits or none.

Your entire response must be only the raw JSON object — no markdown fences, no commentary:

{
  "ungrounded_claims": [{"claim": "", "why": ""}],
  "coverage": [{"requirement": "", "status": "matched|bridged|gap", "note": ""}],
  "edits": [{"old_string": "", "new_string": "", "reason": ""}]
}

---JOB---
