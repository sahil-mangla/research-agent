from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel

from agent.llm_client import call_structured
from agent.schemas.paper import Paper

SYSTEM = """You score how relevant a research paper is to a given problem statement, \
on a 0-10 scale (0 = unrelated, 10 = directly addresses the problem). Judge based on \
the paper's title and abstract/summary only. Be strict: a paper about a related but \
distinct topic should score in the middle, not high."""


class RelevanceScore(BaseModel):
    score: float
    reasoning: str


def _score_one(problem_statement: str, paper: Paper) -> Paper:
    user = (
        f"Problem statement:\n{problem_statement}\n\n"
        f"Paper title: {paper.title}\n"
        f"Paper summary: {paper.tldr or '(no abstract available)'}"
    )
    try:
        result = call_structured(
            system=SYSTEM,
            user=user,
            output_model=RelevanceScore,
            effort="medium",
            max_tokens=512,
        )
        paper.relevance_score = max(0.0, min(10.0, result.score))
    except Exception as exc:
        print(f"[relevance_rank] scoring failed for {paper.title!r}: {exc}")
        paper.relevance_score = 0.0
    return paper


def rank(problem_statement: str, papers: list[Paper], top_n: int = 20, max_workers: int = 8) -> list[Paper]:
    scored: list[Paper] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_score_one, problem_statement, p) for p in papers]
        for future in as_completed(futures):
            scored.append(future.result())

    scored.sort(key=lambda p: p.relevance_score, reverse=True)
    return scored[:top_n]


if __name__ == "__main__":
    from agent.pipeline.query_expansion import expand
    from agent.pipeline.retrieve import retrieve

    problem = "How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?"
    papers = retrieve(expand(problem), per_query_limit=5)
    top = rank(problem, papers, top_n=10)
    for p in top:
        print(f"{p.relevance_score:.1f} — {p.title}")
