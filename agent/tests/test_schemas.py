import pytest
from pydantic import ValidationError

from agent.schemas.opportunity import Feature, Opportunity, SaturationCheck, SupportingPaper
from agent.schemas.paper import Paper, normalize_title


def test_normalize_title_strips_punctuation_and_case():
    assert normalize_title("Lite-RVFL: A Lightweight Network!") == normalize_title(
        "lite rvfl a lightweight network"
    )


def test_paper_dedup_key_matches_normalized_title():
    paper = Paper(title="Some Paper, Title.", source="arxiv")
    assert paper.dedup_key() == normalize_title("Some Paper, Title.")


def test_paper_defaults():
    paper = Paper(title="X", source="arxiv")
    assert paper.authors == []
    assert paper.extracted_limitations == []
    assert paper.citation_count == 0


def _make_opportunity(**overrides) -> Opportunity:
    defaults = dict(
        core_problem="core",
        why_now="why",
        saturation_check=SaturationCheck(
            obvious_solution="obvious", is_saturated=False, differentiation="diff"
        ),
        recommended_solution="solution",
        features=[Feature(feature="f", supports_core_problem="s", priority="core")],
        supporting_papers=[SupportingPaper(title="t", url=None, relevant_finding="finding")],
        feasibility_notes="notes",
        recurrence_signal="signal",
    )
    defaults.update(overrides)
    return Opportunity(**defaults)


def test_opportunity_round_trips_through_model_dump():
    opp = _make_opportunity()
    dumped = opp.model_dump()
    assert Opportunity.model_validate(dumped) == opp


def test_feature_rejects_invalid_priority():
    with pytest.raises(ValidationError):
        Feature(feature="f", supports_core_problem="s", priority="urgent")
