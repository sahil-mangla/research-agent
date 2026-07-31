"""FastAPI layer over run_pipeline — backs the frontend's "Get started" flow.

Runs are executed in a background thread per job; the frontend polls
GET /api/runs/{job_id} for stage progress and, once done, the results.

Falls back to the manual dry-run fixture (real retrieval, canned gaps/synthesis) when
ANTHROPIC_API_KEY isn't set, so the frontend flow is exercisable without a funded key.
"""

import os
import threading
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.main import STAGE_LABELS, run_pipeline
from agent.schemas.opportunity import Opportunity

DRY_RUN = not os.environ.get("ANTHROPIC_API_KEY")
if DRY_RUN:
    from agent.manual_dry_run import run_dry_pipeline

app = FastAPI(title="research-agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


class RunRequest(BaseModel):
    problem_statement: str
    max_papers: int = 15


class RunAck(BaseModel):
    job_id: str


class RunStatus(BaseModel):
    job_id: str
    status: str  # "running" | "done" | "error"
    stage: int
    stage_label: str
    run_id: str | None = None
    opportunities: list[Opportunity] | None = None
    error: str | None = None


def _execute(job_id: str, problem_statement: str, per_query_limit: int) -> None:
    def on_stage(i: int, label: str) -> None:
        with _jobs_lock:
            _jobs[job_id]["stage"] = i
            _jobs[job_id]["stage_label"] = label

    try:
        if DRY_RUN:
            run_id, opportunities = run_dry_pipeline(on_stage=on_stage)
        else:
            run_id, opportunities = run_pipeline(
                problem_statement,
                per_query_limit=per_query_limit,
                on_stage=on_stage,
            )
        with _jobs_lock:
            _jobs[job_id].update(
                status="done",
                stage=len(STAGE_LABELS) - 1,
                run_id=run_id,
                opportunities=[o.model_dump() for o in opportunities],
            )
    except Exception as exc:  # noqa: BLE001 — surface any failure to the frontend
        with _jobs_lock:
            _jobs[job_id].update(status="error", error=str(exc))


@app.post("/api/runs", response_model=RunAck)
def create_run(req: RunRequest) -> RunAck:
    problem_statement = req.problem_statement.strip()
    if not problem_statement:
        raise HTTPException(status_code=400, detail="problem_statement is required")

    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "running",
            "stage": 0,
            "stage_label": STAGE_LABELS[0],
            "run_id": None,
            "opportunities": None,
            "error": None,
        }

    thread = threading.Thread(
        target=_execute,
        args=(job_id, problem_statement, req.max_papers),
        daemon=True,
    )
    thread.start()
    return RunAck(job_id=job_id)


@app.get("/api/runs/{job_id}", response_model=RunStatus)
def get_run(job_id: str) -> RunStatus:
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="unknown job_id")
        return RunStatus(job_id=job_id, **job)
