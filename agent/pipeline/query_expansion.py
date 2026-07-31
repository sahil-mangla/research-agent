from pydantic import BaseModel

from agent.llm_client import call_structured

SYSTEM = """You expand a product/research problem statement into search query variants \
suited for academic search engines (arXiv, Semantic Scholar). Produce 5-10 short, \
keyword-style queries (not full sentences) that cover different angles of the problem: \
the core technical challenge, adjacent subfields, common method names, and alternative \
terminology researchers might use. Avoid overly narrow or overly broad queries."""


class QueryList(BaseModel):
    queries: list[str]


def expand(problem_statement: str) -> list[str]:
    result = call_structured(
        system=SYSTEM,
        user=f"Problem statement:\n{problem_statement}",
        output_model=QueryList,
        effort="medium",
        max_tokens=1024,
    )
    return result.queries


if __name__ == "__main__":
    problem = "How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?"
    for q in expand(problem):
        print("-", q)
