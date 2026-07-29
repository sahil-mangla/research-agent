from pydantic import BaseModel, Field

from agent.llm_client import call_structured
from agent.pipeline.synthesis import GapCluster
from agent.schemas.opportunity import Feature, Opportunity, SaturationCheck, SupportingPaper
from agent.schemas.paper import Paper, normalize_title

DRAFT_SYSTEM = """You write a product/tech opportunity brief anchored to ONE core problem. \
Everything you produce — why_now, recommended_solution, features, feasibility_notes — must \
serve that single core problem. Do not scope-creep into adjacent problems.

Rules:
- core_problem: one sentence, singular focus, no "and"/"as well as" scope-stacking.
- why_now: what recent research shift (from the supporting papers) makes this viable/timely now, \
not a generic market observation.
- recommended_solution: 1-2 sentences, concrete, matching the differentiation from the saturation check \
(not the obvious/saturated solution).
- features: 3-6 features. Each must have priority (core/supporting/optional) and a \
supports_core_problem justification that is SPECIFIC to this problem — not a generic benefit \
that could apply to any product (e.g. "improves user experience" is unacceptable; \
"lets a 3-person team catch drift without standing up Prometheus/Grafana, which the \
underlying papers show is the actual adoption blocker" is acceptable).
- feasibility_notes: name the hardest technical part honestly.
- recurrence_signal: state plainly how many independent papers pointed at this gap."""


class DraftOpportunity(BaseModel):
    core_problem: str
    why_now: str
    recommended_solution: str
    features: list[Feature] = Field(default_factory=list)
    feasibility_notes: str
    recurrence_signal: str


class FeatureVerdict(BaseModel):
    feature: str
    justification_is_weak: bool = Field(
        description="True if supports_core_problem is generic, vague, or could apply to any unrelated product"
    )
    reason: str


class CritiqueResult(BaseModel):
    verdicts: list[FeatureVerdict]


CRITIQUE_SYSTEM = """You are a strict reviewer. For each feature below, judge whether its \
"supports_core_problem" justification is SPECIFIC to the stated core problem, or GENERIC \
(could be copy-pasted onto an unrelated product's feature list unchanged). Flag generic ones \
as weak. Examples of weak/generic justifications: "improves usability", "makes it easier for \
users", "increases engagement", "provides better insights" — these say nothing about THIS \
problem specifically."""


def _draft(cluster: GapCluster, saturation: SaturationCheck) -> DraftOpportunity:
    user = (
        f"Core problem theme: {cluster.tentative_core_problem}\n"
        f"Underlying research gap: {cluster.theme_summary}\n"
        f"Obvious solution (saturated: {saturation.is_saturated}): {saturation.obvious_solution}\n"
        f"Required differentiation: {saturation.differentiation}\n"
        f"Supporting papers: {', '.join(cluster.supporting_paper_titles)}"
    )
    return call_structured(
        system=DRAFT_SYSTEM,
        user=user,
        output_model=DraftOpportunity,
        effort="high",
        max_tokens=4096,
    )


def _enforce_feature_justifications(core_problem: str, features: list[Feature]) -> list[Feature]:
    if not features:
        return features

    feature_list_text = "\n".join(
        f"- feature: {f.feature}\n  supports_core_problem: {f.supports_core_problem}" for f in features
    )
    user = f"Core problem: {core_problem}\n\nFeatures:\n{feature_list_text}"
    try:
        critique = call_structured(
            system=CRITIQUE_SYSTEM,
            user=user,
            output_model=CritiqueResult,
            effort="medium",
            max_tokens=2048,
        )
    except Exception as exc:
        print(f"[opportunity_writer] critique pass failed, keeping all features: {exc}")
        return features

    weak_names = {v.feature for v in critique.verdicts if v.justification_is_weak}
    kept = [f for f in features if f.feature not in weak_names]
    # never let enforcement empty out the feature list entirely — fall back to originals if it would
    return kept if kept else features


def write_opportunity(
    cluster: GapCluster,
    saturation: SaturationCheck,
    papers_by_title: dict[str, Paper],
) -> Opportunity:
    """papers_by_title must be keyed by Paper.dedup_key() (normalized title), not raw title —
    the LLM-generated cluster.supporting_paper_titles may not reproduce titles byte-for-byte."""
    draft = _draft(cluster, saturation)
    kept_features = _enforce_feature_justifications(draft.core_problem, draft.features)

    supporting_papers = []
    for title in cluster.supporting_paper_titles:
        paper = papers_by_title.get(normalize_title(title))
        if paper is None:
            continue
        finding = (paper.extracted_limitations + paper.future_work_notes)
        supporting_papers.append(
            SupportingPaper(
                title=paper.title,
                url=paper.url,
                relevant_finding=finding[0] if finding else cluster.theme_summary,
            )
        )

    return Opportunity(
        core_problem=draft.core_problem,
        why_now=draft.why_now,
        saturation_check=saturation,
        recommended_solution=draft.recommended_solution,
        features=kept_features,
        supporting_papers=supporting_papers,
        feasibility_notes=draft.feasibility_notes,
        recurrence_signal=draft.recurrence_signal,
    )
