from pydantic import BaseModel, Field


def normalize_title(title: str) -> str:
    return "".join(ch.lower() for ch in title if ch.isalnum())


class Paper(BaseModel):
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    source: str  # "arxiv" | "semantic_scholar" | "crossref"
    url: str | None = None
    tldr: str | None = None
    relevance_score: float = 0.0
    citation_count: int = 0
    extracted_limitations: list[str] = Field(default_factory=list)
    future_work_notes: list[str] = Field(default_factory=list)

    def dedup_key(self) -> str:
        return normalize_title(self.title)
