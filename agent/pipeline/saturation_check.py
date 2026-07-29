from agent.llm_client import call_structured
from agent.pipeline.synthesis import GapCluster
from agent.schemas.opportunity import SaturationCheck

SYSTEM = """Given a specific problem theme, identify the OBVIOUS existing solution or \
product category that most people would immediately reach for (e.g. "a dashboard", \
"a digital twin", "a Slack bot", "an off-the-shelf SaaS tool"). Judge honestly whether \
that obvious solution is already saturated (many existing products/startups/open-source \
tools already do this well). Then propose a differentiation that goes one level DEEPER \
than the obvious solution — not a feature bolt-on, but a genuinely different approach \
informed by the underlying research gap. If you are not confident the obvious solution \
is saturated, say so honestly rather than assuming saturation."""


def check(cluster: GapCluster) -> SaturationCheck:
    user = (
        f"Problem theme: {cluster.tentative_core_problem}\n"
        f"Underlying gap: {cluster.theme_summary}"
    )
    return call_structured(
        system=SYSTEM,
        user=user,
        output_model=SaturationCheck,
        effort="high",
        max_tokens=1024,
    )


if __name__ == "__main__":
    from agent.pipeline.synthesis import GapCluster

    sample = GapCluster(
        tentative_core_problem="Small ML teams lack lightweight data drift detection without adopting a full MLOps platform.",
        theme_summary="Papers note existing drift-detection methods assume infrastructure most small teams don't have.",
        supporting_paper_titles=["Example Paper A", "Example Paper B"],
    )
    result = check(sample)
    print(result.model_dump_json(indent=2))
