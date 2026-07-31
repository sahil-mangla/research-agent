from agent.pipeline import retrieve as retrieve_module
from agent.schemas.paper import Paper


def _paper(title, citation_count=0, tldr=None, source="arxiv"):
    return Paper(title=title, source=source, citation_count=citation_count, tldr=tldr)


def test_retrieve_dedupes_by_normalized_title(monkeypatch):
    monkeypatch.setattr(
        retrieve_module.arxiv_client,
        "search",
        lambda query, max_results, since_year: [_paper("Same Title")],
    )
    monkeypatch.setattr(
        retrieve_module.semantic_scholar,
        "search",
        lambda query, max_results, since_year: [_paper("same title.")],
    )

    papers = retrieve_module.retrieve(["q1"], per_query_limit=5)

    assert len(papers) == 1


def test_retrieve_prefers_richer_metadata_on_dedup(monkeypatch):
    monkeypatch.setattr(
        retrieve_module.arxiv_client,
        "search",
        lambda query, max_results, since_year: [_paper("Dup", citation_count=1)],
    )
    monkeypatch.setattr(
        retrieve_module.semantic_scholar,
        "search",
        lambda query, max_results, since_year: [_paper("Dup", citation_count=50)],
    )

    papers = retrieve_module.retrieve(["q1"], per_query_limit=5)

    assert len(papers) == 1
    assert papers[0].citation_count == 50


def test_retrieve_survives_source_failures(monkeypatch):
    def _raise(query, max_results, since_year):
        raise RuntimeError("boom")

    monkeypatch.setattr(retrieve_module.arxiv_client, "search", _raise)
    monkeypatch.setattr(
        retrieve_module.semantic_scholar,
        "search",
        lambda query, max_results, since_year: [_paper("Still Works")],
    )

    papers = retrieve_module.retrieve(["q1"], per_query_limit=5)

    assert len(papers) == 1
    assert papers[0].title == "Still Works"
