import time
import urllib.parse
import xml.etree.ElementTree as ET

import requests

from agent.cache_util import cached_get
from agent.schemas.paper import Paper

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"  # XML namespace URI is opaque — must match the feed exactly, not a live URL
_last_request_time = 0.0
_MIN_INTERVAL = 3.0  # arXiv asks for >=3s between requests


def _throttle() -> None:
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


def _parse_entry(entry: ET.Element) -> Paper | None:
    title_el = entry.find(f"{ATOM_NS}title")
    summary_el = entry.find(f"{ATOM_NS}summary")
    published_el = entry.find(f"{ATOM_NS}published")
    if title_el is None or title_el.text is None:
        return None

    authors = [
        a.findtext(f"{ATOM_NS}name", default="").strip()
        for a in entry.findall(f"{ATOM_NS}author")
    ]
    year = None
    if published_el is not None and published_el.text:
        year = int(published_el.text[:4])

    url = None
    for link in entry.findall(f"{ATOM_NS}link"):
        if link.get("rel") == "alternate":
            url = link.get("href")
            break
    if url is None:
        id_el = entry.find(f"{ATOM_NS}id")
        url = id_el.text if id_el is not None else None

    return Paper(
        title=" ".join(title_el.text.split()),
        authors=[a for a in authors if a],
        year=year,
        source="arxiv",
        url=url,
        tldr=(" ".join(summary_el.text.split()) if summary_el is not None and summary_el.text else None),
    )


def search(query: str, max_results: int = 25, since_year: int | None = None, use_cache: bool = True) -> list[Paper]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    cache_key = f"arxiv:{urllib.parse.urlencode(params)}"

    def fetch():
        _throttle()
        resp = requests.get(ARXIV_API, params=params, timeout=30)
        resp.raise_for_status()
        return resp.text

    xml_text = cached_get(cache_key, fetch) if use_cache else fetch()

    root = ET.fromstring(xml_text)
    papers = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        paper = _parse_entry(entry)
        if paper is None:
            continue
        if since_year is not None and paper.year is not None and paper.year < since_year:
            continue
        papers.append(paper)
    return papers


if __name__ == "__main__":
    results = search("data drift detection machine learning", max_results=5, since_year=2023)
    for p in results:
        print(f"[{p.year}] {p.title} — {p.url}")
