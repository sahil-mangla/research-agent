import hashlib
import json
import os

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")


def cached_get(cache_key: str, fetch_fn):
    """Return cached JSON for cache_key if present, else call fetch_fn(), cache, and return."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    path = os.path.join(CACHE_DIR, f"{digest}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    result = fetch_fn()
    with open(path, "w") as f:
        json.dump(result, f)
    return result
