from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field

from agent.llm_client import call_structured
from agent.schemas.paper import Paper

SYSTEM = """You extract genuine limitations and future-work statements from a research \
paper's title and abstract. Only extract what the abstract itself states or clearly implies \
as unresolved — do not invent limitations that aren't grounded in the text. If the abstract \
gives no explicit signal, return empty lists rather than guessing generically."""


class ExtractedGaps(BaseModel):
    extracted_limitations: list[str] = Field(default_factory=list)
    future_work_notes: list[str] = Field(default_factory=list)


def _extract_one(paper: Paper) -> Paper:
    user = f"Paper title: {paper.title}\n\nAbstract:\n{paper.tldr or '(no abstract available)'}"
    try:
        result = call_structured(
            system=SYSTEM,
            user=user,
            output_model=ExtractedGaps,
            effort="medium",
            max_tokens=1024,
        )
        paper.extracted_limitations = result.extracted_limitations
        paper.future_work_notes = result.future_work_notes
    except Exception as exc:
        print(f"[gap_extraction] failed for {paper.title!r}: {exc}")
    return paper


def extract(papers: list[Paper], max_workers: int = 8) -> list[Paper]:
    results: list[Paper] = []
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_extract_one, p) for p in papers]
        for future in as_completed(futures):
            results.append(future.result())
    return results


if __name__ == "__main__":
    from agent.pipeline.query_expansion import expand
    from agent.pipeline.relevance_rank import rank
    from agent.pipeline.retrieve import retrieve

    problem = "How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?"
    papers = retrieve(expand(problem), per_query_limit=5)
    top = rank(problem, papers, top_n=5)
    for p in extract(top):
        print(p.title)
        print("  limitations:", p.extracted_limitations)
        print("  future work:", p.future_work_notes)
