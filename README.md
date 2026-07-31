# research-agent

[![CI](https://github.com/sahil-mangla/research-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/sahil-mangla/research-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Give it a problem statement. It mines real academic literature for gaps the
authors themselves admit to, clusters recurring gaps into candidate opportunity
themes, and writes each one up as a scoped, evidence-backed product/tech
opportunity brief — complete with a saturation check against the "obvious"
existing solution and features that are justified against the underlying
research rather than generic benefits.

A FastAPI service and React frontend sit on top of the same pipeline so the
flow can be driven from a browser instead of the CLI.

## How it works

`run_pipeline()` in [agent/main.py](agent/main.py) drives six stages, each
backed by a dedicated module and a structured Claude call via
[agent/llm_client.py](agent/llm_client.py):

| Stage | Module | What it does |
|---|---|---|
| 1. Query expansion | [`query_expansion.py`](agent/pipeline/query_expansion.py) | Expands the problem statement into 5–10 keyword-style search variants |
| 2. Retrieval | [`retrieve.py`](agent/pipeline/retrieve.py) | Searches arXiv + Semantic Scholar across all variants, dedupes by normalized title, filters to the last 3 years |
| 3. Relevance ranking | [`relevance_rank.py`](agent/pipeline/relevance_rank.py) | Scores each paper 0–10 against the problem statement, keeps the top N |
| 4. Gap extraction | [`gap_extraction.py`](agent/pipeline/gap_extraction.py) | Pulls only the limitations/future-work statements a paper's abstract actually makes — no invented gaps |
| 5. Synthesis | [`synthesis.py`](agent/pipeline/synthesis.py) | Clusters recurring gaps across papers into narrow, non-overlapping opportunity themes, weighted by supporting-paper count |
| 6. Saturation check + writing | [`saturation_check.py`](agent/pipeline/saturation_check.py), [`opportunity_writer.py`](agent/pipeline/opportunity_writer.py) | Names the obvious existing solution per theme, judges saturation, drafts a differentiated brief, then strips any feature whose justification is generic rather than specific to the core problem |

Results are written to `agent/output/<run_id>.json` and `agent/output/<run_id>.md`.

## Architecture

```
frontend/  (React + Vite)  ──HTTP──▶  agent/server.py  (FastAPI)
                                            │
                                            ▼
                                    agent/main.py: run_pipeline()
                                            │
                              stages 1–6 ──▶ agent/pipeline/*
                                            │
                         agent/sources/*  (arXiv, Semantic Scholar, CrossRef)
                         agent/llm_client.py  (Anthropic structured output)
```

`agent/server.py` runs each request in a background thread and exposes
`POST /api/runs` (starts a run) and `GET /api/runs/{job_id}` (polls stage
progress and, once done, the opportunity briefs) — this is what the frontend's
"Get started" flow talks to.

**Dry-run mode:** if `ANTHROPIC_API_KEY` isn't set, the server automatically
falls back to [`agent/manual_dry_run.py`](agent/manual_dry_run.py), which does
real paper retrieval but substitutes hand-authored gap/synthesis reasoning for
the Claude calls. This makes the full frontend flow exercisable — stage
progression, error states, rendered opportunity cards — without a funded API
key.

## Getting started

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r agent/requirements.txt
cp agent/.env.example agent/.env   # set ANTHROPIC_API_KEY for real (non-dry-run) pipeline calls
```

Run the CLI directly:

```bash
python -m agent.main "How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?"
```

Options: `--max-papers` (per-query-variant limit per source, default 15),
`--output-dir` (default `agent/output/`).

Or serve the API (used by the frontend):

```bash
uvicorn agent.server:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8000` (see
[`frontend/vite.config.ts`](frontend/vite.config.ts)), so run the backend
alongside it. Without `ANTHROPIC_API_KEY` set, runs use dry-run mode
automatically.

## Testing & CI

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs
on every push and pull request against `main`:

| Gate | Command |
|---|---|
| Backend lint | `ruff check agent` |
| Backend types | `mypy agent` |
| Backend tests | `pytest agent/tests` |
| Frontend lint | `npm run lint` (oxlint) |
| Frontend types | `npm run typecheck` (tsc) |
| Frontend tests | `npm run test` (vitest + Testing Library) |

Backend tests cover schema validation, retrieval dedup logic (network calls
mocked), and the FastAPI job lifecycle (pipeline mocked — no live LLM/network
calls in CI). Frontend tests cover the run lifecycle against a mocked `fetch`:
submit-disabled state, the full run-to-rendered-opportunities path, and error
surfacing.

Run everything locally with:

```bash
pip install -r agent/requirements-dev.txt
ruff check agent && mypy agent && pytest agent/tests

cd frontend && npm run lint && npm run typecheck && npm run test
```

## Project layout

```
agent/
  main.py              CLI entrypoint + run_pipeline() orchestrator
  server.py            FastAPI layer over run_pipeline (backs the frontend)
  manual_dry_run.py    Dry-run fixture: real retrieval, canned LLM reasoning
  llm_client.py         Shared Claude structured-output client
  cache_util.py        On-disk response caching for source API calls
  pipeline/            The six pipeline stages
  sources/             arXiv, Semantic Scholar, CrossRef clients
  schemas/             Paper and Opportunity pydantic models
  tests/               pytest suite
frontend/
  src/App.tsx          "Get started" flow: submit, poll, render opportunities
  src/lib/api.ts        Typed fetch client for /api/runs
.github/workflows/     CI pipeline
```

## License

MIT — see [LICENSE](LICENSE).
