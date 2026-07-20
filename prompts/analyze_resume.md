Read the file resume.md and extract a job search profile for the candidate. The candidate can be in any profession — developer, designer, virtual assistant, writer, accountant, marketer, etc. Derive everything from what the resume actually says.

Output ONLY a valid JSON object — no markdown fences, no explanation, no extra text — in this exact shape:

{
  "target_roles": [],
  "key_skills": []
}

Rules:
- target_roles: 4–6 job title variants based on the candidate's actual experience. Examples: a developer resume might yield "Frontend Developer" and "React Developer"; a virtual assistant resume might yield "Virtual Assistant", "Executive Assistant", and "Administrative Assistant".
- key_skills: the top 6–8 skills, tools, or services the candidate is strongest in, extracted from their skills section and work experience (prioritize what appears in both).

Your entire response must be only the raw JSON object — nothing before or after it.
