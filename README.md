# research-agent

A research-to-opportunity agent: give it a problem statement, and it searches academic
literature (arXiv, Semantic Scholar), extracts the gaps and limitations authors admit to,
clusters recurring gaps into candidate opportunity themes, and writes each one up as a
scoped product/tech opportunity brief — complete with a saturation check against the
"obvious" existing solution and features justified against the underlying research, not
generic benefits.

## Pipeline

Each run (`run_pipeline` in [agent/main.py](agent/main.py)) goes through six stages:

1. **Query expansion** ([agent/pipeline/query_expansion.py](agent/pipeline/query_expansion.py)) — expands the problem statement into 5-10 keyword-style search query variants.
2. **Retrieval** ([agent/pipeline/retrieve.py](agent/pipeline/retrieve.py)) — searches arXiv and Semantic Scholar across all query variants, dedupes by normalized title, and filters to the last 3 years.
3. **Relevance ranking** ([agent/pipeline/relevance_rank.py](agent/pipeline/relevance_rank.py)) — scores each paper 0-10 against the problem statement and keeps the top N.
4. **Gap extraction** ([agent/pipeline/gap_extraction.py](agent/pipeline/gap_extraction.py)) — pulls only the limitations/future-work statements a paper's abstract actually makes (no invented gaps).
5. **Synthesis** ([agent/pipeline/synthesis.py](agent/pipeline/synthesis.py)) — clusters recurring gaps across papers into narrow, non-overlapping candidate opportunity themes, weighted by how many independent papers support each.
6. **Saturation check + opportunity writing** ([agent/pipeline/saturation_check.py](agent/pipeline/saturation_check.py), [agent/pipeline/opportunity_writer.py](agent/pipeline/opportunity_writer.py)) — for each theme: names the obvious existing solution and judges whether it's saturated, drafts a differentiated opportunity brief, then runs a critique pass that strips out any feature whose justification is generic rather than specific to the core problem.

Each pipeline stage calls Claude for structured output via [agent/llm_client.py](agent/llm_client.py), which wraps the Anthropic SDK's JSON-schema output mode.

Results are written to `agent/output/<run_id>.json` and `agent/output/<run_id>.md`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r agent/requirements.txt
cp agent/.env.example agent/.env  # set ANTHROPIC_API_KEY
```

## Usage

```bash
python -m agent.main "How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?"
```

Options:
- `--max-papers` — max results per query variant per source (default 15)
- `--output-dir` — where to write the JSON/Markdown report (default `agent/output/`)

## Project layout

- `agent/pipeline/` — the six pipeline stages described above
- `agent/sources/` — API clients for arXiv, Semantic Scholar, and CrossRef (`arxiv_client.py`, `semantic_scholar.py`, `crossref_client.py`)
- `agent/schemas/` — `Paper` and `Opportunity` pydantic models shared across stages
- `agent/cache_util.py` — on-disk response caching for source API calls, to keep repeated dev runs cheap
- `agent/llm_client.py` — shared Claude structured-output client helper
