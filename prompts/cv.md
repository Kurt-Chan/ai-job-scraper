Read resume.md to understand the candidate's full profile — profession, skills, experience, education, and contact details.

Read templates/cv.typ. That file is a **styling reference only** — its sample content (Samir Haddad, a backend engineer) is not the candidate. Copy its preamble and layout conventions exactly; replace every piece of content with the real candidate's.

Below is a JSON object describing a specific job. Write a Typst CV tailored to that job.

Rules:

- **Never invent anything.** Every claim — employer, title, date, tool, metric — must come from resume.md. Tailoring means choosing what to include and how to phrase it, never adding what isn't there.
- Lead with the experience and skills the posting actually asks for. Drop or shorten what's irrelevant to it.
- Mirror the posting's own vocabulary where the resume genuinely supports it (if the resume says "Postgres" and the posting says "PostgreSQL", use the posting's term). Do not claim a skill the resume lacks.
- One page. If it overflows, cut the least relevant bullets — never shrink the font below the template's sizes or drop contact details.
- Keep the contact line as literal text (email, phone, links spelled out), so an ATS text layer can read it.
- Never use `grid` or `columns` for content an ATS must read in order — a grid extracts column-by-column, so labels end up separated from their values. Use one line per item, as the template's Skills section does.
- Keep the section rules and spacing settings from the template verbatim: `block(spacing: 0pt, line(...))` for rules, and `#set list(tight: false, spacing: 0.35em)` — bare `line()` and tight lists both break the layout.
- Escape Typst's markup characters: `@` → `\@`, `$` → `\$`, `~` → `\~` (a bare `~` is a non-breaking space and silently disappears, e.g. "~120 invoices" renders as " 120 invoices"), `#` → `\#`.

Your entire response must be the raw Typst source — starting with `#set page(`, nothing before or after it. No markdown fences, no commentary.

---JOB---
