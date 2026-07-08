Read the file resume.md and extract a job search configuration for the candidate.

Output ONLY a valid JSON object — no markdown fences, no explanation, no extra text — in this exact shape:

{
  "target_roles": [],
  "key_skills": [],
  "search_queries": []
}

Rules:
- target_roles: 4–6 job title variants based on the candidate's actual experience (e.g. "Frontend Developer", "Full Stack Developer", "Next.js Developer", "React Developer")
- key_skills: the top 6–8 technologies the candidate is strongest in, extracted from their skills section and work experience (prioritize what appears in both)
- search_queries: 8–10 Firecrawl-ready search strings combining role titles and skills with site: prefixes. Use OR operators for breadth. Cover at minimum: linkedin.com/jobs, indeed.com, wellfound.com, glassdoor.com, jobstreet.com, onlinejobs.ph. Also include 3 Reddit queries using the groups below. Every query must include the word "remote".

Reddit subreddits to always include (produce exactly 3 grouped queries, one per group):
  - Job boards group: r/jobbit, r/remotejobs, r/WorkOnline
  - Freelance/gig group: r/freelance, r/Upwork
  - Community/dev group: r/webdev, r/digitalnomad, r/remotework

Reddit query format — group subreddits with OR, add "hiring" for community group:
  "(site:reddit.com/r/jobbit OR site:reddit.com/r/remotejobs OR site:reddit.com/r/WorkOnline) (React OR Next.js OR \"Full Stack\") TypeScript remote"
  "(site:reddit.com/r/freelance OR site:reddit.com/r/Upwork) (React OR Next.js OR TypeScript) remote developer"
  "(site:reddit.com/r/webdev OR site:reddit.com/r/digitalnomad OR site:reddit.com/r/remotework) hiring (React OR Next.js OR TypeScript) remote"

Example non-Reddit query format:
  "site:wellfound.com (Next.js OR React) TypeScript remote developer"

Your entire response must be only the raw JSON object — nothing before or after it.
