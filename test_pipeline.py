import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest


def test_discover_pages_interleaves_results_across_queries():
    import agent
    results = {
        "q1": [SimpleNamespace(url=f"https://a.com/{i}", title="", description="") for i in range(3)],
        "q2": [SimpleNamespace(url=f"https://b.com/{i}", title="", description="") for i in range(2)],
        "q3": [],
    }
    fake_app = SimpleNamespace(search=lambda q, limit: SimpleNamespace(web=results[q]))

    pages = agent.discover_pages(fake_app, ["q1", "q2", "q3"])

    assert [p["url"] for p in pages] == [
        "https://a.com/0",
        "https://b.com/0",
        "https://a.com/1",
        "https://b.com/1",
        "https://a.com/2",
    ]


def test_discover_pages_dedupes_regional_subdomains():
    import agent
    results = {
        "q1": [SimpleNamespace(url="https://www.indeed.com/viewjob?jk=abc", title="", description="")],
        "q2": [
            SimpleNamespace(url="https://in.indeed.com/viewjob?jk=abc", title="", description=""),
            SimpleNamespace(url="https://uk.linkedin.com/jobs/view/123", title="", description=""),
        ],
        "q3": [SimpleNamespace(url="https://www.linkedin.com/jobs/view/123", title="", description="")],
    }
    fake_app = SimpleNamespace(search=lambda q, limit: SimpleNamespace(web=results[q]))

    pages = agent.discover_pages(fake_app, ["q1", "q2", "q3"])

    assert [p["url"] for p in pages] == [
        "https://www.indeed.com/viewjob?jk=abc",
        "https://uk.linkedin.com/jobs/view/123",
    ]


def test_canonical_host_leaves_regular_domains_alone():
    import agent
    assert agent._canonical_host("www.indeed.com") == "indeed.com"
    assert agent._canonical_host("ng.indeed.com") == "indeed.com"
    assert agent._canonical_host("ph.jobstreet.com") == "jobstreet.com"
    assert agent._canonical_host("onlinejobs.ph") == "onlinejobs.ph"
    assert agent._canonical_host("glassdoor.co.uk") == "glassdoor.co.uk"
    assert agent._canonical_host("reddit.com") == "reddit.com"


def test_run_pipeline_emits_all_step_events(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "resume.md").write_text("# Resume")
    (tmp_path / "output").mkdir()

    mock_resume_info = {"target_roles": ["Frontend Developer"], "key_skills": ["React"]}
    mock_config = {"search_queries": ["frontend dev remote"]}
    mock_raw_jobs = [{"title": "Dev", "company": "Co", "location": "Remote",
                      "url": "https://example.com", "description": "",
                      "posted_date": "", "source": "example.com"}]
    mock_analyzed = [{"title": "Dev", "company": "Co", "url": "https://example.com",
                      "score": 85, "verdict": "apply", "match_reasons": [],
                      "red_flags": [], "suggested_angle": ""}]

    events = []

    with patch.object(agent, "analyze_resume", return_value=mock_resume_info), \
         patch.object(agent, "build_search_config", return_value=mock_config), \
         patch.object(agent, "scrape_jobs", return_value=mock_raw_jobs), \
         patch.object(agent, "analyze_jobs", return_value=mock_analyzed), \
         patch.object(agent, "generate_cover_letters"):
        result = agent.run_pipeline(on_progress=lambda s, l, st: events.append((s, st)))

    step_statuses = {(s, st) for s, st in events}
    assert (1, "running") in step_statuses
    assert (1, "done") in step_statuses
    assert (2, "running") in step_statuses
    assert (2, "done") in step_statuses
    assert (3, "running") in step_statuses
    assert (3, "done") in step_statuses
    assert (4, "running") in step_statuses
    assert (4, "done") in step_statuses
    assert result == {"total": 1, "above_threshold": 1}


def test_run_pipeline_raises_when_resume_missing(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError, match="Missing resume.md"):
        agent.run_pipeline()


def test_run_pipeline_works_without_callback(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "resume.md").write_text("# Resume")
    (tmp_path / "output").mkdir()

    mock_resume_info = {"target_roles": ["Frontend Developer"], "key_skills": ["React"]}
    mock_config = {"search_queries": ["q"]}
    mock_raw_jobs = [{"title": "Dev", "company": "Co", "location": "Remote",
                      "url": "https://example.com", "description": "",
                      "posted_date": "", "source": "example.com"}]
    mock_analyzed = [{"title": "Dev", "url": "https://example.com", "score": 50,
                      "verdict": "skip", "match_reasons": [], "red_flags": [],
                      "suggested_angle": ""}]

    with patch.object(agent, "analyze_resume", return_value=mock_resume_info), \
         patch.object(agent, "build_search_config", return_value=mock_config), \
         patch.object(agent, "scrape_jobs", return_value=mock_raw_jobs), \
         patch.object(agent, "analyze_jobs", return_value=mock_analyzed), \
         patch.object(agent, "generate_cover_letters"):
        result = agent.run_pipeline()

    assert result["total"] == 1
    assert result["above_threshold"] == 0


def test_analyze_resume_extracts_roles_and_skills():
    import agent
    mock_result = {"target_roles": ["Frontend Developer"], "key_skills": ["React"]}
    with patch.object(agent, "run_claude_json", return_value=mock_result) as mock_call:
        result = agent.analyze_resume()
    assert result == mock_result
    assert mock_call.call_args[0][0] == "prompts/analyze_resume.md"


def test_build_search_config_passes_roles_skills_and_preferences(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    captured = {}

    def fake_run_claude_json(prompt_file, context=""):
        captured["prompt_file"] = prompt_file
        captured["context"] = context
        return {"search_queries": ["q1"]}

    with patch.object(agent, "run_claude_json", side_effect=fake_run_claude_json):
        config = agent.build_search_config(["Frontend Developer"], ["React"], "Egypt, USD, part-time")

    assert captured["prompt_file"] == "prompts/build_queries.md"
    assert "Frontend Developer" in captured["context"]
    assert "React" in captured["context"]
    assert "Egypt, USD, part-time" in captured["context"]
    assert config["target_roles"] == ["Frontend Developer"]
    assert config["key_skills"] == ["React"]
    saved = json.loads((tmp_path / "output" / "search_config.json").read_text())
    assert saved["target_roles"] == ["Frontend Developer"]


def test_build_search_config_omits_preferences_line_when_not_given(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    captured = {}

    def fake_run_claude_json(prompt_file, context=""):
        captured["context"] = context
        return {"search_queries": []}

    with patch.object(agent, "run_claude_json", side_effect=fake_run_claude_json):
        agent.build_search_config(["Frontend Developer"], ["React"])

    assert "Run preferences" not in captured["context"]


def test_run_pipeline_uses_given_resume_info_and_skips_analyze_resume(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "resume.md").write_text("# Resume")
    (tmp_path / "output").mkdir()

    resume_info = {"target_roles": ["Frontend Developer"], "key_skills": ["React"]}
    mock_raw_jobs = [{"title": "Dev", "company": "Co", "location": "Remote",
                      "url": "https://example.com", "description": "",
                      "posted_date": "", "source": "example.com"}]
    mock_analyzed = [{"title": "Dev", "url": "https://example.com", "score": 90,
                      "verdict": "apply", "match_reasons": [], "red_flags": [],
                      "suggested_angle": ""}]
    captured = {}

    def fake_build_search_config(roles, skills, preferences=""):
        captured["roles"] = roles
        captured["skills"] = skills
        captured["preferences"] = preferences
        return {"search_queries": ["q"]}

    def _boom():
        raise AssertionError("analyze_resume should not be called when resume_info is given")

    with patch.object(agent, "analyze_resume", side_effect=_boom), \
         patch.object(agent, "build_search_config", side_effect=fake_build_search_config), \
         patch.object(agent, "scrape_jobs", return_value=mock_raw_jobs), \
         patch.object(agent, "analyze_jobs", return_value=mock_analyzed), \
         patch.object(agent, "generate_cover_letters"):
        agent.run_pipeline(resume_info=resume_info, preferences="Egypt, USD, part-time")

    assert captured == {"roles": ["Frontend Developer"], "skills": ["React"], "preferences": "Egypt, USD, part-time"}


def test_run_claude_json_strips_markdown_fences():
    import agent
    fenced = '```json\n{"target_roles": ["Virtual Assistant"]}\n```'
    with patch.object(agent, "run_claude", return_value=fenced):
        assert agent.run_claude_json("prompts/x.md") == {"target_roles": ["Virtual Assistant"]}


def test_run_claude_json_passes_plain_json_through():
    import agent
    with patch.object(agent, "run_claude", return_value='[{"score": 88}]'):
        assert agent.run_claude_json("prompts/x.md") == [{"score": 88}]


def test_run_claude_json_extracts_json_from_surrounding_prose():
    import agent
    chatty = (
        "I don't have write permission for `output/jobs.json`. Per the task "
        'instructions, here is the raw JSON array:\n\n[{"title": "Support Rep", '
        '"score": 72}]\n\nLet me know if you need anything else.'
    )
    with patch.object(agent, "run_claude", return_value=chatty):
        assert agent.run_claude_json("prompts/x.md") == [{"title": "Support Rep", "score": 72}]


def test_run_claude_json_still_fails_loudly_on_no_json():
    import agent
    with patch.object(agent, "run_claude", return_value="Sorry, I cannot do that."):
        with pytest.raises(RuntimeError, match="invalid JSON"):
            agent.run_claude_json("prompts/x.md")


def test_load_config_returns_defaults_without_file(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    cfg = agent.load_config()
    assert "linkedin.com/jobs" in cfg["job_boards"]
    assert any(g["name"] == "Community" for g in cfg["reddit_groups"])


def test_load_config_overrides_from_file(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"job_boards": ["remoteok.com"]}))
    cfg = agent.load_config()
    assert cfg["job_boards"] == ["remoteok.com"]
    assert cfg["reddit_groups"] == agent.DEFAULT_CONFIG["reddit_groups"]


def test_sources_context_lists_boards_and_groups():
    import agent
    ctx = agent._sources_context({
        "job_boards": ["remoteok.com", "weworkremotely.com"],
        "reddit_groups": [
            {"name": "Dev", "subreddits": ["webdev", "cscareers"], "extra_terms": "hiring"},
            {"name": "Gigs", "subreddits": ["freelance"]},
        ],
    })
    assert "- remoteok.com" in ctx
    assert "- weworkremotely.com" in ctx
    assert "Dev: r/webdev, r/cscareers" in ctx
    assert '"hiring"' in ctx
    assert "Gigs: r/freelance" in ctx


def test_run_claude_raises_when_cli_missing(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "prompt.md").write_text("hello")
    with patch.object(agent.shutil, "which", return_value=None):
        with pytest.raises(RuntimeError, match="claude CLI not found"):
            agent.run_claude("prompt.md")


def test_run_claude_raises_runtime_error_when_exec_fails(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "prompt.md").write_text("hello")

    def _boom(*a, **k):
        raise OSError(8, "Exec format error")

    with patch.object(agent.shutil, "which", return_value="/home/user/.npm-global/bin/claude"), \
         patch.object(agent.subprocess, "run", side_effect=_boom):
        with pytest.raises(RuntimeError, match="failed to run"):
            agent.run_claude("prompt.md")


def test_run_claude_uses_resolved_executable(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "prompt.md").write_text("hello")
    fake_result = SimpleNamespace(returncode=0, stdout="ok\n", stderr="")
    with patch.object(agent.shutil, "which", return_value="/usr/local/bin/claude"), \
         patch.object(agent.subprocess, "run", return_value=fake_result) as mock_run:
        out = agent.run_claude("prompt.md")
    assert out == "ok"
    assert mock_run.call_args[0][0][0] == "/usr/local/bin/claude"


def test_extract_postings_uses_firecrawl_when_it_succeeds():
    import agent
    page = {"url": "https://indeed.com/job/1", "title": "snippet title", "description": "snippet desc"}
    fake_app = SimpleNamespace(scrape=lambda *a, **k: SimpleNamespace(
        json={"jobs": [{"title": "Dev", "company": "Co", "url": "/job/1"}]}
    ))

    postings = agent.extract_postings(fake_app, exa=None, page=page)

    assert postings == [{
        "title": "Dev", "company": "Co", "location": "Remote",
        "url": "https://indeed.com/job/1", "description": "", "posted_date": "",
        "source": "indeed.com",
    }]


def test_extract_postings_falls_back_to_exa_when_firecrawl_fails():
    import agent

    def _boom(*a, **k):
        raise RuntimeError("Website Not Supported")

    fake_app = SimpleNamespace(scrape=_boom)
    fake_exa = SimpleNamespace(get_contents=lambda urls, summary: SimpleNamespace(
        results=[SimpleNamespace(summary=json.dumps({"jobs": [{"title": "Dev", "company": "Co"}]}))]
    ))
    page = {"url": "https://www.linkedin.com/jobs/view/1", "title": "t", "description": "d"}

    postings = agent.extract_postings(fake_app, exa=fake_exa, page=page)

    assert postings[0]["title"] == "Dev"
    assert postings[0]["source"] == "linkedin.com"


def test_extract_postings_falls_back_to_snippet_when_exa_also_fails():
    import agent

    def _boom(*a, **k):
        raise RuntimeError("Website Not Supported")

    fake_app = SimpleNamespace(scrape=_boom)
    fake_exa = SimpleNamespace(get_contents=_boom)
    page = {"url": "https://www.linkedin.com/jobs/view/1", "title": "snippet title", "description": "d"}

    postings = agent.extract_postings(fake_app, exa=fake_exa, page=page)

    assert postings == [{
        "title": "snippet title", "company": "", "location": "Remote",
        "url": "https://www.linkedin.com/jobs/view/1", "description": "d",
        "posted_date": "", "source": "linkedin.com",
    }]


def test_extract_postings_skips_exa_when_not_configured():
    import agent

    def _boom(*a, **k):
        raise RuntimeError("Website Not Supported")

    fake_app = SimpleNamespace(scrape=_boom)
    page = {"url": "https://www.linkedin.com/jobs/view/1", "title": "snippet title", "description": "d"}

    postings = agent.extract_postings(fake_app, exa=None, page=page)

    assert postings[0]["title"] == "snippet title"


def test_analyze_jobs_writes_jobs_json(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()

    analyzed = [{"title": "Dev", "score": 85, "verdict": "apply"}]
    with patch.object(agent, "run_claude", return_value=json.dumps(analyzed)):
        result = agent.analyze_jobs()

    assert result == analyzed
    assert json.loads((tmp_path / "output" / "jobs.json").read_text()) == analyzed


def test_analyze_jobs_includes_preferences_in_context(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    captured = {}

    def fake_run_claude(prompt_file, context=""):
        captured["context"] = context
        return "[]"

    with patch.object(agent, "run_claude", side_effect=fake_run_claude):
        agent.analyze_jobs(preferences="Egypt, USD, part-time")

    assert "Egypt, USD, part-time" in captured["context"]
