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

    mock_config = {"search_queries": ["frontend dev remote"]}
    mock_raw_jobs = [{"title": "Dev", "company": "Co", "location": "Remote",
                      "url": "https://example.com", "description": "",
                      "posted_date": "", "source": "example.com"}]
    mock_analyzed = [{"title": "Dev", "company": "Co", "url": "https://example.com",
                      "score": 85, "verdict": "apply", "match_reasons": [],
                      "red_flags": [], "suggested_angle": ""}]

    events = []

    with patch.object(agent, "build_search_config", return_value=mock_config), \
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

    mock_config = {"search_queries": ["q"]}
    mock_raw_jobs = [{"title": "Dev", "company": "Co", "location": "Remote",
                      "url": "https://example.com", "description": "",
                      "posted_date": "", "source": "example.com"}]
    mock_analyzed = [{"title": "Dev", "url": "https://example.com", "score": 50,
                      "verdict": "skip", "match_reasons": [], "red_flags": [],
                      "suggested_angle": ""}]

    with patch.object(agent, "build_search_config", return_value=mock_config), \
         patch.object(agent, "scrape_jobs", return_value=mock_raw_jobs), \
         patch.object(agent, "analyze_jobs", return_value=mock_analyzed), \
         patch.object(agent, "generate_cover_letters"):
        result = agent.run_pipeline()

    assert result["total"] == 1
    assert result["above_threshold"] == 0


def test_run_claude_json_strips_markdown_fences():
    import agent
    fenced = '```json\n{"target_roles": ["Virtual Assistant"]}\n```'
    with patch.object(agent, "run_claude", return_value=fenced):
        assert agent.run_claude_json("prompts/x.md") == {"target_roles": ["Virtual Assistant"]}


def test_run_claude_json_passes_plain_json_through():
    import agent
    with patch.object(agent, "run_claude", return_value='[{"score": 88}]'):
        assert agent.run_claude_json("prompts/x.md") == [{"score": 88}]


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


def test_analyze_jobs_writes_jobs_json(tmp_path, monkeypatch):
    import agent
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()

    analyzed = [{"title": "Dev", "score": 85, "verdict": "apply"}]
    with patch.object(agent, "run_claude", return_value=json.dumps(analyzed)):
        result = agent.analyze_jobs()

    assert result == analyzed
    assert json.loads((tmp_path / "output" / "jobs.json").read_text()) == analyzed
