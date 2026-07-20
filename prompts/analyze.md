Read resume.md to understand the candidate's full profile — profession, skills, experience, seniority, location, and preferences. The candidate can be in any profession; judge every job against what the resume actually shows.
Then read output/raw_jobs.json.

For each job, score it 0–100 based on how well it matches THIS specific candidate:

Scoring factors:
- Skills match: award high points if the job requires skills, tools, or services the candidate's resume demonstrates
- Seniority fit: infer the candidate's level from their years of experience and role history in the resume; weight roles at or slightly above that level favorably, avoid roles far below or far above it
- Remote-first signals: explicit "remote" in title or description, async culture mentioned, timezone compatible with the candidate's location (from the resume)
- Posting freshness: award points if the job was posted within the last 30 days (use today's date provided at the end of this prompt) and the role is still open; penalize or skip listings that are expired, closed, or posted more than 30 days ago
- Preferences: honor any preferences stated in the resume (industries, company types or sizes, tools or stacks to avoid), AND any run preferences given at the end of this prompt (e.g. target location/country, desired pay currency or rate, employment type such as full-time/part-time/contract/hourly)
- Red flags: requires physical presence or relocation, citizenship or work-authorization restrictions the candidate doesn't meet, core requirements entirely outside the candidate's skill set, posting is closed or older than 30 days, or conflicts with stated run preferences (e.g. full-time only when the candidate wants part-time/hourly)

Location matching is strict, not a soft preference. If run preferences state a target location (e.g. a specific country or "worldwide remote"), and a job's title, description, or requirements name a *different* specific country/region as a requirement (e.g. "(India)" in the title, "must be based in the Philippines", "candidates must reside in the US") — that is disqualifying. Cap the score at 40 and set verdict to "skip", regardless of how well the skills match. Do NOT infer a location mismatch from the URL/domain alone (e.g. a job scraped from an Indian job-board mirror like in.indeed.com or glassdoor.co.in) — judge only by what the posting's own content requires; many such postings are genuinely open to any remote location.

Include only jobs with score >= 60.

Your entire response must be only the raw JSON array — no markdown fences, no explanation, nothing before or after it:

[{
  "title": "",
  "company": "",
  "url": "",
  "score": 0,
  "verdict": "apply|review|skip",
  "match_reasons": [],
  "red_flags": [],
  "suggested_angle": ""
}]

suggested_angle: one sentence on how the candidate should frame their application for this specific role, based on their resume.
