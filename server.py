import json
import queue
import threading
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

app = FastAPI()

STATUS_FILE = Path("output/status.json")
JOBS_FILE = Path("output/jobs.json")
COVER_LETTERS_DIR = Path("output/cover_letters")
CVS_DIR = Path("output/cvs")

run_lock = threading.Lock()


def _read_status() -> dict:
    if STATUS_FILE.exists():
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    return {}


def _write_status(data: dict) -> None:
    STATUS_FILE.parent.mkdir(exist_ok=True)
    STATUS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


@app.get("/")
async def index():
    return FileResponse("ui/index.html")


@app.get("/api/jobs")
async def get_jobs():
    if not JOBS_FILE.exists():
        return JSONResponse([])
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    status = _read_status()
    for job in jobs:
        job["status"] = status.get(job.get("url", ""), "none")
    return JSONResponse(jobs)


class StatusUpdate(BaseModel):
    url: str
    status: str


@app.post("/api/status")
async def update_status(body: StatusUpdate):
    if body.status not in ("applied", "skipped", "none"):
        raise HTTPException(status_code=400, detail="status must be applied, skipped, or none")
    data = _read_status()
    if body.status == "none":
        data.pop(body.url, None)
    else:
        data[body.url] = body.status
    _write_status(data)
    from agent import set_application_status
    set_application_status(body.url, body.status)
    return {"ok": True}


@app.get("/api/cover-letter")
async def get_cover_letter(company: str = Query(...), title: str = Query(...)):
    from agent import _slug
    slug = f"{_slug(company)}__{_slug(title)}"
    path = COVER_LETTERS_DIR / f"{slug}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Cover letter not found")
    return {"content": path.read_text(encoding="utf-8")}


@app.get("/api/cv")
async def get_cv(company: str = Query(...), title: str = Query(...)):
    from agent import _slug
    path = CVS_DIR / f"{_slug(company)}__{_slug(title)}.pdf"
    if not path.exists():
        raise HTTPException(status_code=404, detail="CV not found")
    return FileResponse(path, media_type="application/pdf")


@app.get("/api/apply")
async def apply(url: str = Query(...)):
    """Run the drafter-reviewer apply stage for one job, streaming progress."""
    if not JOBS_FILE.exists():
        raise HTTPException(status_code=404, detail="No jobs yet — run the pipeline first.")
    jobs = json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    job = next((j for j in jobs if j.get("url") == url), None)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    q: queue.Queue = queue.Queue()

    def _apply_thread() -> None:
        try:
            from agent import apply_to_job
            result = apply_to_job(job, on_progress=lambda label: q.put({"step": label}))
            q.put({"step": "complete", **result})
        except Exception as exc:
            q.put({"step": "error", "message": str(exc)})
        finally:
            q.put(None)

    threading.Thread(target=_apply_thread, daemon=True).start()

    async def _event_stream():
        import asyncio
        loop = asyncio.get_running_loop()
        while True:
            event = await loop.run_in_executor(None, q.get)
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


@app.get("/api/resume-roles")
async def get_resume_roles():
    from agent import RESUME_FILE, analyze_resume
    if not Path(RESUME_FILE).exists():
        raise HTTPException(status_code=400, detail=f"Missing {RESUME_FILE} — add your resume before running.")
    try:
        return analyze_resume()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/run")
async def run_agent(
    roles: list[str] = Query(default=[]),
    skills: list[str] = Query(default=[]),
    preferences: str = "",
    find_more: bool = False,
):
    if not run_lock.acquire(blocking=False):
        async def _busy():
            yield f"data: {json.dumps({'step': 'busy'})}\n\n"
        return StreamingResponse(_busy(), media_type="text/event-stream")

    resume_info = {"target_roles": roles, "key_skills": skills} if roles else None

    q: queue.Queue = queue.Queue()

    def _on_progress(step: int, label: str, status: str) -> None:
        q.put({"step": step, "label": label, "status": status})

    def _pipeline_thread() -> None:
        try:
            from agent import run_pipeline
            result = run_pipeline(on_progress=_on_progress, resume_info=resume_info,
                                  preferences=preferences, find_more=find_more)
            q.put({"step": "complete", **result})
        except Exception as exc:
            q.put({"step": "error", "message": str(exc)})
        finally:
            run_lock.release()
            q.put(None)

    threading.Thread(target=_pipeline_thread, daemon=True).start()

    async def _event_stream():
        import asyncio
        loop = asyncio.get_running_loop()
        while True:
            event = await loop.run_in_executor(None, q.get)
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
