Read resume.md to understand the candidate's full profile — skills, experience, seniority, and preferences.
Then read output/raw_jobs.json.

For each job, score it 0–100 based on how well it matches THIS specific candidate:

Scoring factors:
- Stack match: award high points if the job requires skills the candidate has (Next.js, React, TypeScript, Convex, Tailwind, etc.)
- Seniority fit: the candidate has ~3 years of experience — weight mid-level or "senior" roles favorably, avoid pure junior or staff/principal
- Remote-first signals: explicit "remote" in title or description, async culture mentioned, global/Philippines-friendly timezone
- Company stage: startups and mid-size preferred; deprioritize large enterprise
- Posting freshness: award points if the job was posted within the last 30 days (use today's date provided at the end of this prompt) and the role is still open; penalize or skip listings that are expired, closed, or posted more than 30 days ago
- Red flags: requires physical presence, Java/.NET-only stack, no TypeScript, US/EU citizens only, posting is closed or older than 30 days

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
