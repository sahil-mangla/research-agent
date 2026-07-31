import time

from fastapi.testclient import TestClient

from agent import server
from agent.schemas.opportunity import Feature, Opportunity, SaturationCheck, SupportingPaper

client = TestClient(server.app)


def _fake_opportunity() -> Opportunity:
    return Opportunity(
        core_problem="core",
        why_now="why",
        saturation_check=SaturationCheck(obvious_solution="o", is_saturated=True, differentiation="d"),
        recommended_solution="solution",
        features=[Feature(feature="f", supports_core_problem="s", priority="core")],
        supporting_papers=[SupportingPaper(title="t", url=None, relevant_finding="finding")],
        feasibility_notes="notes",
        recurrence_signal="signal",
    )


def _fake_pipeline(*args, on_stage=None, **kwargs):
    if on_stage is not None:
        for i, label in enumerate(server.STAGE_LABELS):
            on_stage(i, label)
    return "test-run-id", [_fake_opportunity()]


def test_create_run_rejects_blank_problem_statement():
    resp = client.post("/api/runs", json={"problem_statement": "   "})
    assert resp.status_code == 400


def test_get_run_404_for_unknown_job():
    resp = client.get("/api/runs/does-not-exist")
    assert resp.status_code == 404


def test_run_lifecycle_reaches_done(monkeypatch):
    monkeypatch.setattr(server, "DRY_RUN", True, raising=False)
    monkeypatch.setattr(server, "run_dry_pipeline", _fake_pipeline, raising=False)

    resp = client.post("/api/runs", json={"problem_statement": "test problem"})
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    for _ in range(50):
        status = client.get(f"/api/runs/{job_id}").json()
        if status["status"] != "running":
            break
        time.sleep(0.05)

    assert status["status"] == "done"
    assert status["run_id"] == "test-run-id"
    assert len(status["opportunities"]) == 1
    assert status["opportunities"][0]["core_problem"] == "core"


def test_run_lifecycle_surfaces_pipeline_error(monkeypatch):
    def _failing_pipeline(*args, on_stage=None, **kwargs):
        raise RuntimeError("pipeline exploded")

    monkeypatch.setattr(server, "DRY_RUN", True, raising=False)
    monkeypatch.setattr(server, "run_dry_pipeline", _failing_pipeline, raising=False)

    resp = client.post("/api/runs", json={"problem_statement": "test problem"})
    job_id = resp.json()["job_id"]

    for _ in range(50):
        status = client.get(f"/api/runs/{job_id}").json()
        if status["status"] != "running":
            break
        time.sleep(0.05)

    assert status["status"] == "error"
    assert "pipeline exploded" in status["error"]
