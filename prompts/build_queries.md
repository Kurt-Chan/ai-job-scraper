Build Firecrawl-ready search queries for a job search. The candidate's selected target roles and key skills are given below — use them as-is, do not invent new ones.

Output ONLY a valid JSON object — no markdown fences, no explanation, no extra text — in this exact shape:

{
  "search_queries": []
}

Rules:
- search_queries: search strings combining the given role titles and skills with site: prefixes. Use OR operators for breadth. Produce exactly one query per job board listed at the end of this prompt, plus exactly one grouped query per Reddit subreddit group listed there.
- If run preferences are given below (e.g. location/country, pay currency or rate, employment type such as part-time/contract/hourly), fold them into every query in place of a generic "remote" keyword — e.g. a preference of "Egypt, paid in USD, part-time" should produce queries containing terms like "Egypt" OR "remote", "USD", "part-time" OR "contract" rather than just "remote".
- If no run preferences are given, every query must include the word "remote".

Reddit query format — combine the subreddits of one group with OR, and include the group's extra terms if it has any:
  "(site:reddit.com/r/jobbit OR site:reddit.com/r/remotejobs OR site:reddit.com/r/WorkOnline) (React OR Next.js OR \"Full Stack\") TypeScript remote"

Example job board query formats:
  "site:wellfound.com (Next.js OR React) TypeScript remote developer"
  "site:onlinejobs.ph (\"Virtual Assistant\" OR \"Executive Assistant\") \"calendar management\" remote"

Your entire response must be only the raw JSON object — nothing before or after it. The candidate's selected roles and skills, any run preferences, and the job boards and Reddit groups to cover follow below.
