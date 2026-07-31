"""Research-to-Opportunity Agent — CLI entrypoint.

`run_pipeline()` is the reusable orchestration function — a future frontend/API layer
should import and call it directly rather than shelling out to this CLI.
"""

import argparse
import datetime
import json
import os
from typing import Callable

from agent.pipeline.gap_extraction import extract
from agent.pipeline.opportunity_writer import write_opportunity
from agent.pipeline.query_expansion import expand
from agent.pipeline.relevance_rank import rank
from agent.pipeline.retrieve import retrieve
from agent.pipeline.saturation_check import check
from agent.pipeline.synthesis import synthesize
from agent.schemas.opportunity import Opportunity

DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


STAGE_LABELS = [
    "Expand query",
    "Retrieve papers",
    "Rank relevance",
    "Extract gaps",
    "Synthesize themes",
    "Write briefs",
]


def run_pipeline(
    problem_statement: str,
    per_query_limit: int = 15,
    top_n_papers: int = 20,
    min_opportunities: int = 3,
    max_opportunities: int = 5,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    on_stage: Callable[[int, str], None] | None = None,
) -> tuple[str, list[Opportunity]]:
    def stage(i: int) -> None:
        if on_stage is not None:
            on_stage(i, STAGE_LABELS[i])

    stage(0)
    print("[1/6] Expanding query...")
    queries = expand(problem_statement)

    stage(1)
    print(f"[2/6] Retrieving papers across {len(queries)} query variants...")
    papers = retrieve(queries, per_query_limit=per_query_limit)
    print(f"       {len(papers)} deduped papers found")

    stage(2)
    print("[3/6] Ranking relevance...")
    ranked = rank(problem_statement, papers, top_n=top_n_papers)

    stage(3)
    print("[4/6] Extracting gaps/limitations...")
    papers_with_gaps = extract(ranked)
    papers_by_title = {p.dedup_key(): p for p in papers_with_gaps}

    stage(4)
    print("[5/6] Synthesizing opportunity clusters...")
    clusters = synthesize(problem_statement, papers_with_gaps)
    clusters.sort(key=lambda c: len(c.supporting_paper_titles), reverse=True)
    selected = clusters[:max_opportunities]

    if len(selected) < min_opportunities:
        print(
            f"       Warning: only {len(selected)} candidate opportunities survived synthesis "
            f"(target was {min_opportunities}-{max_opportunities}). Proceeding with what the evidence supports."
        )

    stage(5)
    print(f"[6/6] Writing {len(selected)} opportunities (saturation check + feature enforcement)...")
    opportunities: list[Opportunity] = []
    for cluster in selected:
        saturation = check(cluster)
        opportunities.append(write_opportunity(cluster, saturation, papers_by_title))

    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs(output_dir, exist_ok=True)
    _write_json(run_id, output_dir, problem_statement, opportunities)
    _write_markdown(run_id, output_dir, problem_statement, opportunities)

    return run_id, opportunities


def _write_json(run_id: str, output_dir: str, problem_statement: str, opportunities: list[Opportunity]) -> None:
    path = os.path.join(output_dir, f"{run_id}.json")
    payload = {
        "run_id": run_id,
        "problem_statement": problem_statement,
        "opportunities": [o.model_dump() for o in opportunities],
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)


def _write_markdown(run_id: str, output_dir: str, problem_statement: str, opportunities: list[Opportunity]) -> None:
    path = os.path.join(output_dir, f"{run_id}.md")
    lines = ["# Research-to-Opportunity Report", "", f"**Problem statement:** {problem_statement}", ""]

    for i, opp in enumerate(opportunities, 1):
        lines += [
            f"## {i}. {opp.core_problem}",
            "",
            f"**Why now:** {opp.why_now}",
            "",
            f"**Recurrence signal:** {opp.recurrence_signal}",
            "",
            "### Saturation check",
            f"- Obvious solution: {opp.saturation_check.obvious_solution}",
            f"- Saturated: {'yes' if opp.saturation_check.is_saturated else 'no'}",
            f"- Differentiation: {opp.saturation_check.differentiation}",
            "",
            "### Recommended solution",
            opp.recommended_solution,
            "",
            "### Features",
            "",
            "| Feature | Priority | Supports core problem |",
            "|---|---|---|",
        ]
        for feat in opp.features:
            lines.append(f"| {feat.feature} | {feat.priority} | {feat.supports_core_problem} |")
        lines += ["", "### Supporting papers", ""]
        for p in opp.supporting_papers:
            url_part = f" — {p.url}" if p.url else ""
            lines.append(f"- **{p.title}**{url_part}\n  - {p.relevant_finding}")
        lines += ["", "### Feasibility notes", opp.feasibility_notes, "", "---", ""]

    with open(path, "w") as f:
        f.write("\n".join(lines))


def _main() -> None:
    parser = argparse.ArgumentParser(description="Research-to-Opportunity Agent")
    parser.add_argument("problem_statement", help="The problem statement to research")
    parser.add_argument("--max-papers", type=int, default=15, dest="per_query_limit")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    run_id, opportunities = run_pipeline(
        args.problem_statement,
        per_query_limit=args.per_query_limit,
        output_dir=args.output_dir,
    )
    print(f"\nDone. Wrote {len(opportunities)} opportunities to {args.output_dir}/{run_id}.{{json,md}}")


if __name__ == "__main__":
    _main()
