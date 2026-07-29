import urllib.parse

import requests

from agent.cache_util import cached_get

CROSSREF_API = "https://api.crossref.org/works"


def lookup(title: str, authors: list[str] | None = None, use_cache: bool = True) -> dict | None:
    """Backfill DOI/metadata for a paper by title. Returns the best-matching CrossRef work or None."""
    params = {"query.bibliographic": title, "rows": 1}
    cache_key = f"crossref:{urllib.parse.urlencode(params)}"

    def fetch():
        resp = requests.get(CROSSREF_API, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    data = cached_get(cache_key, fetch) if use_cache else fetch()

    items = data.get("message", {}).get("items", [])
    if not items:
        return None
    return items[0]


if __name__ == "__main__":
    result = lookup("Attention Is All You Need")
    print(result.get("DOI") if result else "not found")
