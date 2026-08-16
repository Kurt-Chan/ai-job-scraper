import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "ui").mkdir()
    (tmp_path / "ui" / "index.html").write_text("<html><body>UI</body></html>")
    (tmp_path / "output").mkdir()
    import importlib, server
    importlib.reload(server)
    return TestClient(server.app)


def test_index_returns_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "UI" in res.text


def test_get_jobs_empty_when_no_file(client):
    res = client.get("/api/jobs")
    assert res.status_code == 200
    assert res.json() == []


def test_get_jobs_merges_status(client, tmp_path):
    jobs = [{"title": "Dev", "company": "Co", "url": "https://example.com",
             "score": 85, "verdict": "apply"}]
    (tmp_path / "output" / "jobs.json").write_text(json.dumps(jobs))
    (tmp_path / "output" / "status.json").write_text(
        json.dumps({"https://example.com": "applied"})
    )
    res = client.get("/api/jobs")
    data = res.json()
    assert data[0]["status"] == "applied"


def test_get_jobs_status_defaults_to_none(client, tmp_path):
    jobs = [{"title": "Dev", "url": "https://example.com", "score": 85}]
    (tmp_path / "output" / "jobs.json").write_text(json.dumps(jobs))
    res = client.get("/api/jobs")
    assert res.json()[0]["status"] == "none"


def test_post_status_saves_applied(client, tmp_path):
    res = client.post("/api/status",
                      json={"url": "https://example.com", "status": "applied"})
    assert res.status_code == 200
    data = json.loads((tmp_path / "output" / "status.json").read_text())
    assert data["https://example.com"] == "applied"


def test_post_status_none_removes_entry(client, tmp_path):
    (tmp_path / "output" / "status.json").write_text(
        json.dumps({"https://example.com": "applied"})
    )
    client.post("/api/status", json={"url": "https://example.com", "status": "none"})
    data = json.loads((tmp_path / "output" / "status.json").read_text())
    assert "https://example.com" not in data


def test_post_status_rejects_invalid_value(client):
    res = client.post("/api/status",
                      json={"url": "https://example.com", "status": "maybe"})
    assert res.status_code == 400


def test_cover_letter_found(client, tmp_path):
    (tmp_path / "output" / "cover_letters").mkdir()
    slug = "tech-holding__frontend-engineer-contract-remote"
    (tmp_path / "output" / "cover_letters" / f"{slug}.md").write_text("Dear hiring manager,")
    res = client.get("/api/cover-letter?company=Tech+Holding&title=Frontend+Engineer+%28Contract%29+-+Remote")
    assert res.status_code == 200
    assert "Dear hiring manager" in res.json()["content"]


def test_cover_letter_not_found(client):
    res = client.get("/api/cover-letter?company=Nobody&title=Nothing")
    assert res.status_code == 404


def test_resume_roles_returns_400_when_resume_missing(client):
    res = client.get("/api/resume-roles")
    assert res.status_code == 400


def test_resume_roles_returns_target_roles_and_skills(client, tmp_path, monkeypatch):
    (tmp_path / "resume.md").write_text("# Resume")
    import agent
    monkeypatch.setattr(agent, "analyze_resume", lambda: {"target_roles": ["Dev"], "key_skills": ["Python"]})
    res = client.get("/api/resume-roles")
    assert res.status_code == 200
    assert res.json() == {"target_roles": ["Dev"], "key_skills": ["Python"]}


def test_resume_roles_returns_500_on_claude_failure(client, tmp_path, monkeypatch):
    (tmp_path / "resume.md").write_text("# Resume")
    import agent

    def boom():
        raise RuntimeError("Claude returned invalid JSON")

    monkeypatch.setattr(agent, "analyze_resume", boom)
    res = client.get("/api/resume-roles")
    assert res.status_code == 500


def test_run_passes_roles_skills_and_preferences_to_pipeline(client, monkeypatch):
    import agent
    captured = {}

    def fake_run_pipeline(on_progress=None, resume_info=None, preferences="", find_more=False):
        captured["resume_info"] = resume_info
        captured["preferences"] = preferences
        captured["find_more"] = find_more
        return {"total": 0, "above_threshold": 0}

    monkeypatch.setattr(agent, "run_pipeline", fake_run_pipeline)
    res = client.get("/api/run", params=[
        ("roles", "Frontend Developer"), ("skills", "React"), ("preferences", "Egypt, USD"),
    ])

    assert res.status_code == 200
    assert captured["resume_info"] == {"target_roles": ["Frontend Developer"], "key_skills": ["React"]}
    assert captured["preferences"] == "Egypt, USD"
    assert captured["find_more"] is False


def test_run_forwards_find_more_to_the_pipeline(client, monkeypatch):
    import agent
    captured = {}

    def fake_run_pipeline(on_progress=None, resume_info=None, preferences="", find_more=False):
        captured["find_more"] = find_more
        return {"total": 0, "above_threshold": 0}

    monkeypatch.setattr(agent, "run_pipeline", fake_run_pipeline)
    client.get("/api/run", params={"find_more": "true"})

    assert captured["find_more"] is True


def test_run_uses_auto_detected_roles_when_none_given(client, monkeypatch):
    import agent
    captured = {}

    def fake_run_pipeline(on_progress=None, resume_info=None, preferences="", find_more=False):
        captured["resume_info"] = resume_info
        return {"total": 0, "above_threshold": 0}

    monkeypatch.setattr(agent, "run_pipeline", fake_run_pipeline)
    res = client.get("/api/run")

    assert res.status_code == 200
    assert captured["resume_info"] is None


def test_cv_found(client, tmp_path):
    (tmp_path / "output" / "cvs").mkdir()
    (tmp_path / "output" / "cvs" / "tech-co__backend-engineer.pdf").write_bytes(b"%PDF-1.7")
    res = client.get("/api/cv?company=Tech+Co&title=Backend+Engineer")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"


def test_cv_not_found(client):
    assert client.get("/api/cv?company=Nobody&title=Nothing").status_code == 404


def test_apply_streams_progress_and_result(client, tmp_path, monkeypatch):
    job = {"company": "Co", "title": "Dev", "url": "https://x/1", "score": 90}
    (tmp_path / "output" / "jobs.json").write_text(json.dumps([job]))

    import agent
    monkeypatch.setattr(agent, "apply_to_job", lambda j, on_progress=None: (
        on_progress("Drafting"), {"slug": "co__dev", "draft": "d", "revised": "r",
                                  "review": {"edits": []}, "skipped_edits": []})[1])

    res = client.get("/api/apply?url=https://x/1")
    assert res.status_code == 200
    assert '"step": "Drafting"' in res.text
    assert '"revised": "r"' in res.text


def test_apply_404s_for_an_unknown_job(client, tmp_path):
    (tmp_path / "output" / "jobs.json").write_text(json.dumps([]))
    assert client.get("/api/apply?url=https://nope").status_code == 404


def test_apply_404s_before_any_pipeline_run(client):
    assert client.get("/api/apply?url=https://x/1").status_code == 404


def test_apply_reports_errors_over_the_stream(client, tmp_path, monkeypatch):
    (tmp_path / "output" / "jobs.json").write_text(json.dumps([{"url": "https://x/1"}]))

    import agent
    def boom(job, on_progress=None):
        raise RuntimeError("claude exploded")
    monkeypatch.setattr(agent, "apply_to_job", boom)

    res = client.get("/api/apply?url=https://x/1")
    assert '"step": "error"' in res.text
    assert "claude exploded" in res.text


def test_post_status_marks_the_tracked_application(client, tmp_path):
    import agent
    agent.record_application({"company": "Co", "title": "Dev", "url": "https://x/1"})

    client.post("/api/status", json={"url": "https://x/1", "status": "applied"})

    rows = (tmp_path / "output" / "applications.csv").read_text()
    assert "applied" in rows
