from pydantic import BaseModel, Field

from agent.llm_client import call_structured
from agent.schemas.paper import Paper

SYSTEM = """You cluster recurring gaps/limitations across a set of research papers into \
distinct candidate opportunity themes. Each theme must center on ONE specific, narrow \
problem (not a broad research area) that multiple papers independently point at. \
Weight themes by how many independent papers support them — a gap mentioned by only \
one paper is weaker signal than one mentioned by several. Produce as many distinct, \
non-overlapping themes as the evidence genuinely supports (do not force a fixed count), \
but favor precision over quantity: merge themes that are really the same underlying gap."""


class GapCluster(BaseModel):
    tentative_core_problem: str = Field(description="Single sentence, narrow, specific problem")
    theme_summary: str = Field(description="What the recurring gap actually is, in 1-2 sentences")
    supporting_paper_titles: list[str] = Field(description="Titles of papers whose gaps feed this cluster")


class ClusterList(BaseModel):
    clusters: list[GapCluster]


def _format_papers_for_prompt(papers: list[Paper]) -> str:
    lines = []
    for p in papers:
        if not p.extracted_limitations and not p.future_work_notes:
            continue
        lines.append(f"### {p.title} ({p.year})")
        if p.extracted_limitations:
            lines.append("Limitations: " + "; ".join(p.extracted_limitations))
        if p.future_work_notes:
            lines.append("Future work: " + "; ".join(p.future_work_notes))
        lines.append("")
    return "\n".join(lines)


def synthesize(problem_statement: str, papers: list[Paper]) -> list[GapCluster]:
    papers_text = _format_papers_for_prompt(papers)
    if not papers_text.strip():
        return []

    user = (
        f"Original problem statement (for context, clusters need not match it exactly):\n"
        f"{problem_statement}\n\n"
        f"Extracted gaps from papers:\n{papers_text}"
    )
    result = call_structured(
        system=SYSTEM,
        user=user,
        output_model=ClusterList,
        effort="high",
        max_tokens=4096,
    )
    return result.clusters


if __name__ == "__main__":
    from agent.pipeline.gap_extraction import extract
    from agent.pipeline.query_expansion import expand
    from agent.pipeline.relevance_rank import rank
    from agent.pipeline.retrieve import retrieve

    problem = "How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?"
    papers = extract(rank(problem, retrieve(expand(problem), per_query_limit=5), top_n=8))
    for c in synthesize(problem, papers):
        print(c.tentative_core_problem, "—", len(c.supporting_paper_titles), "papers")
