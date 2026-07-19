# agent.py
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from itertools import zip_longest
from pathlib import Path
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

# ── config ──────────────────────────────────────────────
THRESHOLD = 70
RESUME_FILE = "resume.md"
CONFIG_FILE = "config.json"

# Where to search. config.json (same shape) overrides these defaults, so the
# job boards and subreddits can be tailored without editing code or prompts.
DEFAULT_CONFIG = {
    "job_boards": [
        "linkedin.com/jobs",
        "indeed.com",
        "wellfound.com",
        "glassdoor.com",
        "jobstreet.com",
        "onlinejobs.ph",
    ],
    "reddit_groups": [
        {"name": "Job boards", "subreddits": ["jobbit", "remotejobs", "WorkOnline"]},
        {"name": "Freelance/gig", "subreddits": ["freelance", "Upwork"]},
        {
            "name": "Community",
            "subreddits": ["forhire", "digitalnomad", "remotework"],
            "extra_terms": "hiring",
        },
    ],
}

# Stage 2 (scrape) limits — a search hit is often a listing/category page
# (e.g. ph.jobstreet.com/nextjs-jobs) that contains many postings. We scrape
# each discovered URL and extract the individual postings from it. Cap the
# number of pages scraped per run so credit usage stays bounded.
MAX_PAGES_TO_SCRAPE = 20
SCRAPE_TIMEOUT_MS = 120000  # listing pages (JobStreet, LinkedIn) are JS-heavy

# What Firecrawl should pull out of each scraped page.
EXTRACT_PROMPT = (
    "Extract every individual job posting on this page. For each posting capture "
    "the job title, the hiring company, the location, the direct URL to that "
    "specific posting (not this listing/search page), the date it was posted, and "
    "a short description. If the page is already a single job posting, return just "
    "that one. Ignore navigation links, ads, related searches, and other pages."
)
JOB_EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "jobs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company": {"type": "string"},
                    "location": {"type": "string"},
                    "url": {
                        "type": "string",
                        "description": "Direct link to the individual job posting.",
                    },
                    "posted_date": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["title"],
            },
        }
    },
    "required": ["jobs"],
}

# ── search sources config ─────────────────────────────────
def load_config() -> dict:
    """Return the search-sources config: DEFAULT_CONFIG overridden by any
    top-level keys present in config.json."""
    cfg = dict(DEFAULT_CONFIG)
    path = Path(CONFIG_FILE)
    if path.exists():
        cfg.update(json.loads(path.read_text(encoding="utf-8")))
    return cfg

def _sources_context(cfg: dict) -> str:
    """Render the configured job boards and subreddit groups as prompt context
    for prompts/build_queries.md."""
    boards = "\n".join(f"- {b}" for b in cfg.get("job_boards", []))
    groups = []
    for g in cfg.get("reddit_groups", []):
        line = f"- {g['name']}: " + ", ".join(f"r/{s}" for s in g.get("subreddits", []))
        if g.get("extra_terms"):
            line += f' (also include the term "{g["extra_terms"]}" in the query)'
        groups.append(line)
    return (
        "\nJob boards to cover (one query each):\n"
        + boards
        + "\n\nReddit subreddit groups (one grouped query each):\n"
        + "\n".join(groups)
    )

# ── step 0: build search config from resume ───────────────
def build_search_config() -> dict:
    """Ask Claude to extract search config from the resume."""
    config = run_claude_json("prompts/build_queries.md", context=_sources_context(load_config()))
    Path("output/search_config.json").write_text(json.dumps(config, indent=2))
    print(f"  Roles: {config.get('target_roles')}")
    print(f"  Skills: {config.get('key_skills')}")
    print(f"  Queries ({len(config.get('search_queries', []))}): ready")
    return config

# ── url canonicalization ──────────────────────────────────
def _canonical_host(host: str) -> str:
    """Collapse www. and two-letter regional prefixes (in.indeed.com,
    uk.linkedin.com, ph.jobstreet.com) so one site isn't treated as many."""
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    labels = host.split(".")
    if len(labels) >= 3 and len(labels[0]) == 2:
        host = ".".join(labels[1:])
    return host

def _dedup_key(url: str) -> str:
    """Key for URL deduplication: canonical host + path + query."""
    p = urlparse(url)
    return f"{_canonical_host(p.netloc)}{p.path}?{p.query}"

# ── step 1a: discover candidate pages via search ─────────
def discover_pages(app: "FirecrawlApp", search_queries: list[str]) -> list[dict]:
    """Run each search query and return unique candidate pages.

    A page may be a single posting OR a listing/category page that contains
    many postings — stage 1b sorts that out by scraping.

    Results are interleaved round-robin across queries (first hit of each
    query, then second of each, ...) so the MAX_PAGES_TO_SCRAPE cap doesn't
    starve sources whose queries run later in the list.
    """
    seen_urls: set[str] = set()
    results_per_query: list[list[dict]] = []

    for query in search_queries:
        print(f"  Searching: {query[:70]}...")
        hits: list[dict] = []
        try:
            response = app.search(query, limit=10)
            for r in response.web or []:
                url = r.url
                if not url or _dedup_key(url) in seen_urls:
                    continue
                seen_urls.add(_dedup_key(url))
                hits.append({
                    "url": url,
                    "title": r.title or "",
                    "description": r.description or "",
                })
        except Exception as e:
            print(f"  Query failed: {e}")
        print(f"    {len(hits)} new result(s)")
        results_per_query.append(hits)

    return [page for group in zip_longest(*results_per_query) for page in group if page]

# ── step 1b: scrape each page and extract individual postings ─
def extract_postings(app: "FirecrawlApp", page: dict) -> list[dict]:
    """Scrape one page and extract the individual job postings it contains.

    Falls back to the search snippet (treated as a single posting) if the
    scrape fails or the page yields no structured postings, so we never lose
    a result that was already an individual posting.
    """
    listing_url = page["url"]
    source = _canonical_host(urlparse(listing_url).netloc)

    def _snippet_fallback() -> list[dict]:
        return [{
            "title": page["title"],
            "company": "",
            "location": "Remote",
            "url": listing_url,
            "description": page["description"],
            "posted_date": "",
            "source": source,
        }]

    try:
        doc = app.scrape(
            listing_url,
            formats=[{"type": "json", "prompt": EXTRACT_PROMPT, "schema": JOB_EXTRACT_SCHEMA}],
            only_main_content=True,
            timeout=SCRAPE_TIMEOUT_MS,
        )
    except Exception as e:
        print(f"    Scrape failed ({source}): {e} — keeping search snippet")
        return _snippet_fallback()

    data = doc.json if isinstance(doc.json, dict) else {}
    raw_postings = data.get("jobs") or []
    if not raw_postings:
        return _snippet_fallback()

    postings: list[dict] = []
    for p in raw_postings:
        if not isinstance(p, dict) or not (p.get("title") or "").strip():
            continue
        # Resolve the posting URL relative to the page; fall back to the page URL.
        posting_url = (p.get("url") or "").strip()
        posting_url = urljoin(listing_url, posting_url) if posting_url else listing_url
        postings.append({
            "title": p.get("title", "").strip(),
            "company": (p.get("company") or "").strip(),
            "location": (p.get("location") or "Remote").strip() or "Remote",
            "url": posting_url,
            "description": (p.get("description") or "").strip(),
            "posted_date": (p.get("posted_date") or "").strip(),
            "source": source,
        })
    return postings or _snippet_fallback()

# ── step 1: search → scrape → individual postings ─────────
def scrape_jobs(search_queries: list[str]) -> list[dict]:
    app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])

    pages = discover_pages(app, search_queries)
    print(f"  Discovered {len(pages)} candidate pages; scraping up to {MAX_PAGES_TO_SCRAPE}...")

    seen_urls: set[str] = set()
    jobs: list[dict] = []
    for page in pages[:MAX_PAGES_TO_SCRAPE]:
        print(f"  Scraping: {page['url'][:70]}...")
        for job in extract_postings(app, page):
            url = job["url"]
            if not url or _dedup_key(url) in seen_urls:
                continue
            seen_urls.add(_dedup_key(url))
            jobs.append(job)

    return jobs

# ── claude runner ─────────────────────────────────────────
def run_claude(prompt_file: str, context: str = "") -> str:
    """Run a Claude prompt file and return the text result.
    Read tool is allowed so Claude can read resume/jobs files.
    Write tool is not allowed, forcing Claude to print output instead.
    Optional context is appended to the prompt for inline data injection.
    """
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    if context:
        prompt = prompt + "\n" + context
    # Resolve the executable so Windows finds the claude.cmd/claude.exe shim.
    claude_exe = shutil.which("claude")
    if not claude_exe:
        raise RuntimeError(
            "claude CLI not found on PATH — install Claude Code and make sure "
            "`claude` runs from a terminal."
        )
    result = subprocess.run(
        [claude_exe, "-p", prompt, "--output-format", "text", "--allowedTools", "Read"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=".",
    )
    if result.returncode != 0:
        print(f"Claude error: {result.stderr}")
        raise RuntimeError("Claude subprocess failed")
    return result.stdout.strip()

def run_claude_json(prompt_file: str, context: str = ""):
    """Run a Claude prompt that must return JSON, and parse it."""
    raw = run_claude(prompt_file, context)
    if not raw:
        raise RuntimeError(f"Claude returned empty output for {prompt_file}")
    # Claude occasionally wraps output in ```json fences despite instructions.
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*\s*\n", "", raw)
        raw = re.sub(r"\n```\s*$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Claude returned invalid JSON for {prompt_file}: {e}\n---\n{raw[:300]}")

# ── step 2: analyze scraped jobs via Claude ───────────────
def analyze_jobs() -> list[dict]:
    """Run Claude analysis on raw_jobs.json and write output/jobs.json."""
    today = datetime.now().strftime("%Y-%m-%d")
    all_jobs = run_claude_json("prompts/analyze.md", context=f"Today's date is {today}.")
    Path("output/jobs.json").write_text(json.dumps(all_jobs, indent=2))
    return all_jobs

# ── cover letters ─────────────────────────────────────────
def _slug(text: str, max_len: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:max_len]

def generate_cover_letters(jobs: list[dict]):
    out_dir = Path("output/cover_letters")
    out_dir.mkdir(parents=True, exist_ok=True)

    for job in jobs:
        company = job.get("company") or "unknown"
        title = job.get("title") or "role"
        slug = f"{_slug(company)}__{_slug(title)}"
        out_path = out_dir / f"{slug}.md"

        print(f"  Writing cover letter: {company} — {title[:50]}...")
        try:
            letter = run_claude("prompts/cover_letter.md", context=json.dumps(job, indent=2))
            out_path.write_text(letter, encoding="utf-8")
        except Exception as e:
            print(f"  Failed for {slug}: {e}")

# ── pipeline orchestrator ──────────────────────────────────
def run_pipeline(on_progress=None) -> dict:
    """Run the full 4-step pipeline.

    Calls on_progress(step, label, status) at each stage where:
      step   — int 1-4
      label  — human-readable step name
      status — "running" or "done"

    Returns {"total": int, "above_threshold": int}.
    Raises RuntimeError on any failure.
    """
    def emit(step, label, status):
        if on_progress:
            on_progress(step, label, status)

    Path("output").mkdir(exist_ok=True)

    if not Path(RESUME_FILE).exists():
        raise RuntimeError(f"Missing {RESUME_FILE} — add your resume before running.")

    emit(1, "Building search config", "running")
    config = build_search_config()
    search_queries = config.get("search_queries", [])
    if not search_queries:
        raise RuntimeError("No search queries generated — check prompts/build_queries.md")
    emit(1, "Building search config", "done")

    emit(2, "Scraping jobs", "running")
    jobs = scrape_jobs(search_queries)
    if not jobs:
        raise RuntimeError("No jobs found — check your FIRECRAWL_API_KEY or search queries.")
    Path("output/raw_jobs.json").write_text(json.dumps(jobs, indent=2))
    emit(2, "Scraping jobs", "done")

    emit(3, "Analyzing & scoring", "running")
    all_jobs = analyze_jobs()
    emit(3, "Analyzing & scoring", "done")

    emit(4, "Generating cover letters", "running")
    good_jobs = [j for j in all_jobs if j.get("score", 0) >= THRESHOLD]
    apply_jobs = [j for j in good_jobs if j.get("verdict") == "apply"]
    if apply_jobs:
        generate_cover_letters(apply_jobs)
    emit(4, "Generating cover letters", "done")

    return {"total": len(all_jobs), "above_threshold": len(good_jobs)}

# ── main pipeline ─────────────────────────────────────────
def run():
    def print_progress(step, label, status):
        if status == "running":
            print(f"\nStep {step}: {label}...")

    try:
        result = run_pipeline(on_progress=print_progress)
        print(f"\nDone! {result['above_threshold']} of {result['total']} jobs above threshold ({THRESHOLD})")
    except RuntimeError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
