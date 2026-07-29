import os
import urllib.parse

import requests

from agent.cache_util import cached_get
from agent.schemas.paper import Paper

S2_SEARCH_API = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "title,abstract,tldr,year,citationCount,fieldsOfStudy,url,authors"


def _headers() -> dict:
    key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    return {"x-api-key": key} if key else {}


def _parse_result(item: dict) -> Paper:
    tldr = None
    if item.get("tldr") and item["tldr"].get("text"):
        tldr = item["tldr"]["text"]
    elif item.get("abstract"):
        tldr = item["abstract"]

    authors = [a.get("name", "") for a in (item.get("authors") or [])]

    return Paper(
        title=item.get("title") or "",
        authors=[a for a in authors if a],
        year=item.get("year"),
        source="semantic_scholar",
        url=item.get("url"),
        tldr=tldr,
        citation_count=item.get("citationCount") or 0,
    )


def search(query: str, max_results: int = 25, since_year: int | None = None, use_cache: bool = True) -> list[Paper]:
    params = {"query": query, "fields": FIELDS, "limit": min(max_results, 100)}
    if since_year is not None:
        params["year"] = f"{since_year}-"

    cache_key = f"s2:{urllib.parse.urlencode(params)}"

    def fetch():
        resp = requests.get(S2_SEARCH_API, params=params, headers=_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    data = cached_get(cache_key, fetch) if use_cache else fetch()

    return [_parse_result(item) for item in data.get("data", []) if item.get("title")]


if __name__ == "__main__":
    results = search("data drift detection machine learning", max_results=5, since_year=2023)
    for p in results:
        print(f"[{p.year}] {p.title} (cites={p.citation_count}) — {p.url}")
