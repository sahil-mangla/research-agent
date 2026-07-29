import datetime

from agent.schemas.paper import Paper
from agent.sources import arxiv_client, semantic_scholar

YEARS_BACK = 3


def _since_year() -> int:
    return datetime.date.today().year - YEARS_BACK


def retrieve(queries: list[str], per_query_limit: int = 15) -> list[Paper]:
    """Search arXiv + Semantic Scholar across all query variants, dedup by title, filter to last N years."""
    since_year = _since_year()
    all_papers: list[Paper] = []

    for query in queries:
        try:
            all_papers.extend(arxiv_client.search(query, max_results=per_query_limit, since_year=since_year))
        except Exception as exc:
            print(f"[retrieve] arXiv search failed for {query!r}: {exc}")
        try:
            all_papers.extend(semantic_scholar.search(query, max_results=per_query_limit, since_year=since_year))
        except Exception as exc:
            print(f"[retrieve] Semantic Scholar search failed for {query!r}: {exc}")

    seen: dict[str, Paper] = {}
    for paper in all_papers:
        key = paper.dedup_key()
        if not key:
            continue
        existing = seen.get(key)
        if existing is None:
            seen[key] = paper
        else:
            # prefer the record with richer metadata (citation count / tldr present)
            if paper.citation_count > existing.citation_count or (paper.tldr and not existing.tldr):
                seen[key] = paper

    return list(seen.values())


if __name__ == "__main__":
    from agent.pipeline.query_expansion import expand

    qs = expand("How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?")
    papers = retrieve(qs, per_query_limit=5)
    print(f"Retrieved {len(papers)} deduped papers")
    for p in papers[:10]:
        print(f"[{p.year}] ({p.source}) {p.title}")
