from typing import Literal

from pydantic import BaseModel, Field


class SaturationCheck(BaseModel):
    obvious_solution: str
    is_saturated: bool
    differentiation: str


class Feature(BaseModel):
    feature: str
    supports_core_problem: str
    priority: Literal["core", "supporting", "optional"]


class SupportingPaper(BaseModel):
    title: str
    url: str | None = None
    relevant_finding: str


class Opportunity(BaseModel):
    core_problem: str
    why_now: str
    saturation_check: SaturationCheck
    recommended_solution: str
    features: list[Feature] = Field(default_factory=list)
    supporting_papers: list[SupportingPaper] = Field(default_factory=list)
    feasibility_notes: str
    recurrence_signal: str
