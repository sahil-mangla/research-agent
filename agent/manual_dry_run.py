"""One-off manual dry run: real retrieval + real Pydantic models + real output writers,
with the Anthropic API calls replaced by hand-authored reasoning (no funded API key available).
Not part of the shipped pipeline — delete after review, or keep as a fixture example."""

from typing import Callable, TypedDict

from agent.main import STAGE_LABELS, _write_json, _write_markdown
from agent.pipeline.retrieve import retrieve
from agent.pipeline.synthesis import GapCluster
from agent.schemas.opportunity import Feature, Opportunity, SaturationCheck, SupportingPaper
from agent.schemas.paper import normalize_title


class _Draft(TypedDict):
    core_problem: str
    why_now: str
    recommended_solution: str
    features: list[Feature]
    feasibility_notes: str
    recurrence_signal: str
    weak_features: list[str]

PROBLEM_STATEMENT = "How can small teams detect data drift in production ML pipelines without a dedicated MLOps platform?"

QUERIES = [
    "data drift detection lightweight",
    "concept drift monitoring machine learning production",
    "ML model monitoring small teams",
    "statistical drift detection without MLOps",
    "covariate shift detection deployment",
    "drift detection open source tools",
    "model performance monitoring resource constrained",
    "distribution shift detection production systems",
]

# --- manually extracted gaps, grounded in the actual abstracts fetched during this run ---
GAPS: dict[str, tuple[list[str], list[str]]] = {
    "Lite-RVFL: A Lightweight Random Vector Functional-Link Neural Network for Learning Under Concept Drift": (
        ["Adapts to drift without explicit drift detection, so it provides no signal/alert that drift occurred",
         "Validated only on a single real-world safety-assessment task, not a broad benchmark"], []),
    "Interpretable Anomaly and Drift Detection with Gaussian Mixture Models": (
        ["The interpretable unexplained-mass statistic fails to detect drift that is a pure re-weighting of existing regimes (only MMD catches that case)",
         "GMM detector is rarely more accurate than baseline anomaly detectors, trading some accuracy for interpretability"], []),
    "Time to Retrain? Detecting Concept Drifts in Machine Learning Systems": (
        ["Prior SOTA semi-supervised drift detectors require significant labeling effort and only work for certain ML model types",
         "CDSeer still requires some manual labeling (about 1% of full supervision), not fully label-free"], []),
    "Unsupervised Concept Drift Detection from Deep Learning Representations in Real-time": (
        ["Prior unsupervised drift detectors were too computationally intensive for real-time large-scale production, or failed to explain drift",
         "DriftLens underperformed previous methods in 2 of 17 evaluated use cases",
         "Designed specifically for deep learning classifiers on unstructured data, not general/tabular ML models"], []),
    "How to Sustainably Monitor ML-Enabled Systems? Accuracy and Energy Efficiency Tradeoffs in Concept Drift Detection": (
        ["No single concept-drift detector is both highly accurate and low-energy — practitioners must trade off accuracy against energy cost",
         "Evaluated only on synthetic datasets with six base classifiers, not validated on live production systems"], []),
    "Label-Free Concept Drift Assessment for Reliable AI in Emerging Wireless Applications": (
        ["Evaluated only on two wireless-specific application domains (fingerprinting localization, link-anomaly detection); generality to other ML domains unverified"], []),
    "Estimating Model Performance Under Covariate Shift Without Labels": (
        ["Existing proxy/drift-detection methods fail to adequately measure the actual performance impact of covariate shift",
         "PAPE is scoped to binary classification on unlabeled tabular data only — not validated for multi-class or unstructured-data models"], []),
    "WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales": (
        ["Prior nonparametric sequential-testing monitoring methods can detect shifts but cannot diagnose the cause of degradation or distinguish concept shift from extreme covariate shift"], []),
    "Open-Source Drift Detection Tools in Action: Insights from Two Use Cases": (
        ["No single open-source drift-detection tool (Evidently AI, NannyML, Alibi-Detect) covers both general drift detection AND precise shift-timing/impact analysis — teams must combine tools or accept gaps"], []),
    "A Self-Organizing Clustering System for Unsupervised Distribution Shift Detection": (
        ["Classic distribution-shift detection tools (PCA, kernel-PCA) are sensitive to outliers/noise and rely on rigid algebraic assumptions",
         "Method validated only on curated benchmark datasets (MNIST, sensor data, ozone levels), not live production deployment"], []),
    "Sequential Harmful Shift Detection Without Labels": (
        ["Requires training and maintaining a separate error-estimator model to serve as a label-free proxy — adds infrastructure overhead"], []),
    "Towards Differentiating Between Failures and Domain Shifts in Industrial Data Streams": (
        ["Standard anomaly/failure detectors incorrectly flag normal domain shifts (e.g. a new product line) as failures, causing false alarms",
         "Final differentiation between failure and domain shift still requires a human operator in the loop, not fully automated",
         "Validated on a single industrial case study (steel factory data stream)"], []),
}

CLUSTERS = [
    GapCluster(
        tentative_core_problem=(
            "Small ML teams must stitch together multiple specialized drift-detection tools because "
            "no single lightweight tool covers both general detection AND diagnosing the cause/impact of a shift."
        ),
        theme_summary=(
            "Across open-source tool benchmarks and monitoring frameworks, no individual solution combines "
            "general drift detection, precise shift-timing/impact analysis, and low compute cost — teams are "
            "forced into multi-tool stacks or accuracy/energy tradeoffs they can't easily reason about."
        ),
        supporting_paper_titles=[
            "Open-Source Drift Detection Tools in Action: Insights from Two Use Cases",
            "WATCH: Adaptive Monitoring for AI Deployments via Weighted-Conformal Martingales",
            "Time to Retrain? Detecting Concept Drifts in Machine Learning Systems",
            "How to Sustainably Monitor ML-Enabled Systems? Accuracy and Energy Efficiency Tradeoffs in Concept Drift Detection",
        ],
    ),
    GapCluster(
        tentative_core_problem=(
            "Small teams running mixed or tabular production models have no validated label-free drift "
            "detection method, since existing 'label-free' research is scoped to narrow domains or still "
            "requires partial labels or a separately-trained proxy model."
        ),
        theme_summary=(
            "Papers claiming label-free or unsupervised drift detection either still require partial labeling, "
            "need to train and maintain a separate proxy/error-estimator model, or were validated only in a "
            "narrow domain (wireless, deep-learning classifiers, binary tabular classification) — generality "
            "to typical small-team production stacks is unverified."
        ),
        supporting_paper_titles=[
            "Label-Free Concept Drift Assessment for Reliable AI in Emerging Wireless Applications",
            "Estimating Model Performance Under Covariate Shift Without Labels",
            "Sequential Harmful Shift Detection Without Labels",
            "Time to Retrain? Detecting Concept Drifts in Machine Learning Systems",
            "Unsupervised Concept Drift Detection from Deep Learning Representations in Real-time",
        ],
    ),
    GapCluster(
        tentative_core_problem=(
            "Drift detectors routinely misclassify benign, expected distribution changes as failures, causing "
            "alert fatigue that erodes trust in monitoring for teams without dedicated MLOps staff to triage alerts."
        ),
        theme_summary=(
            "Multiple papers independently show that naive drift/anomaly detectors cannot distinguish a harmful "
            "shift from a normal domain evolution, either failing outright on certain shift types or still "
            "requiring a human operator to make the final call — a burden small teams can't absorb."
        ),
        supporting_paper_titles=[
            "Towards Differentiating Between Failures and Domain Shifts in Industrial Data Streams",
            "Interpretable Anomaly and Drift Detection with Gaussian Mixture Models",
            "A Self-Organizing Clustering System for Unsupervised Distribution Shift Detection",
        ],
    ),
]

SATURATIONS = [
    SaturationCheck(
        obvious_solution="A drift-monitoring dashboard/SaaS platform (e.g. Evidently AI, NannyML, Arize, WhyLabs)",
        is_saturated=True,
        differentiation=(
            "Rather than another dashboard, ship a single lightweight library that auto-selects the right "
            "detector per situation and auto-routes: a cheap always-on general drift signal, and only when it "
            "fires, automatically run shift-timing/impact analysis on just the affected window — combining what "
            "D3Bench shows are two separately-excelling tools into one adaptive pipeline stage, not a UI."
        ),
    ),
    SaturationCheck(
        obvious_solution="An unsupervised/label-free drift-detection algorithm library",
        is_saturated=False,
        differentiation=(
            "Instead of one more narrowly-validated label-free detector, build a thin proxy-label adapter: "
            "automatically train a lightweight error-estimator from whatever weak signal small teams already "
            "have (business KPIs, delayed ground truth, spot-checks) and use it to make ANY existing detector "
            "effectively label-free for the team's specific model type — a wrapper, not a new algorithm."
        ),
    ),
    SaturationCheck(
        obvious_solution="A configurable alert-severity/threshold system to reduce false alarms",
        is_saturated=True,
        differentiation=(
            "Threshold tuning still puts triage on a human. Instead, auto-tag each detected shift as 'benign "
            "domain evolution' vs 'likely failure' using structural signals (correlation with known deploy/"
            "data-source-change events, whether the shift is a re-weighting of known regimes vs. genuinely "
            "novel) — closing the loop the industrial paper shows still needs a human."
        ),
    ),
]

# --- manually drafted opportunities, each with one deliberately generic feature to verify the
# enforcement critique pass actually removes it ---
DRAFTS: list[_Draft] = [
    dict(
        core_problem=CLUSTERS[0].tentative_core_problem,
        why_now=(
            "D3Bench (2024) just empirically confirmed that today's best open-source tools split the job — "
            "one is best at general detection, another at pinpointing timing/impact — while a separate "
            "2024 energy-tradeoff study shows most 'accurate' detectors are too costly to run continuously; "
            "combining the two research threads makes an adaptive, cost-aware two-stage detector newly "
            "buildable rather than requiring a bespoke platform."
        ),
        recommended_solution=(
            "A single Python library that runs a cheap always-on general drift detector, and only when it "
            "fires, automatically triggers a more expensive shift-timing/impact analysis on just the flagged "
            "window — giving small teams the combined coverage D3Bench shows currently requires two separate "
            "tools, at a fraction of the always-on compute cost."
        ),
        features=[
            Feature(feature="Two-stage detector: cheap always-on screen + expensive on-demand timing/impact analysis",
                     supports_core_problem="Directly implements the differentiation from the saturation check — mirrors what D3Bench shows Evidently AI and NannyML do separately, but triggered adaptively so small teams get both without running the expensive analysis continuously.",
                     priority="core"),
            Feature(feature="Per-detector energy/accuracy profile picker seeded from the 2024 tradeoff study's published detector rankings",
                     supports_core_problem="Removes the guesswork the source paper shows practitioners currently face — a team with no MLOps staff can pick a detector by declared budget instead of running their own 420-combination study.",
                     priority="core"),
            Feature(feature="Clean, modern user interface with dark mode",
                     supports_core_problem="Improves user experience and makes the tool more pleasant to use daily.",
                     priority="optional"),
            Feature(feature="Single pip-installable package with no external service dependency",
                     supports_core_problem="Directly targets 'without a dedicated MLOps platform' — the whole opportunity is about avoiding infra a small team can't staff, so zero-infra install is load-bearing, not incidental.",
                     priority="core"),
            Feature(feature="Exportable window-level report tagged with which detector fired and why",
                     supports_core_problem="Gives the team an audit trail that Lite-RVFL's silent-adaptation approach explicitly lacks — without this, the two-stage pipeline is a black box like the tools it's replacing.",
                     priority="supporting"),
        ],
        feasibility_notes=(
            "The hard part isn't the detectors themselves (published, benchmarked) — it's building a reliable "
            "trigger/handoff between stage 1 and stage 2 that doesn't miss slow, gradual drift the cheap "
            "detector under-weights (the energy-tradeoff paper shows cheap detectors like HDDM_A/PageHinkley/"
            "DDM/EDDM have poor accuracy, so stage 1 can't be too cheap or it defeats the purpose)."
        ),
        recurrence_signal="4 independent papers (D3Bench, WATCH, CDSeer/Time to Retrain, and the concept-drift energy-efficiency study) point at the same underlying gap: no single lightweight tool covers both detection and diagnosis.",
        weak_features=["Clean, modern user interface with dark mode"],
    ),
    dict(
        core_problem=CLUSTERS[1].tentative_core_problem,
        why_now=(
            "Three 2024-2025 papers independently built label-free/proxy-based detectors for different narrow "
            "domains using the same underlying trick — a trained error-estimator or pseudo-label proxy — which "
            "means the pattern is now provable enough to generalize into a domain-agnostic wrapper, rather than "
            "each team re-deriving it for their own model type."
        ),
        recommended_solution=(
            "A thin adapter layer that trains a lightweight proxy error-estimator from whatever weak signal a "
            "team already has (a business KPI, delayed ground truth, or periodic spot-checks) and plugs that "
            "proxy into any existing statistical drift detector — making detectors that assume labels usable "
            "in a label-scarce small-team setting, instead of shipping yet another narrowly-validated detector."
        ),
        features=[
            Feature(feature="Proxy error-estimator trainer that ingests any weak/delayed signal and outputs a pseudo-label stream",
                     supports_core_problem="This is the exact mechanism the harmful-shift-detection paper shows works for label-free settings, generalized beyond its original narrow use case — it's the core unlock, not a nice-to-have.",
                     priority="core"),
            Feature(feature="Adapter interface so any labeled-assuming detector (ADWIN, DDM, PageHinkley) can consume the proxy stream unmodified",
                     supports_core_problem="Directly solves the domain-narrowness gap identified across the three source papers — teams keep using well-understood, published detectors instead of adopting an unproven wireless- or vision-specific one.",
                     priority="core"),
            Feature(feature="Confidence score on the proxy's own reliability, surfaced alongside every drift alert",
                     supports_core_problem="Without this, teams can't tell whether an alert reflects real drift or proxy noise — the CFPT paper's own approach explicitly filters low-confidence pseudo-labels for exactly this reason, so omitting it would undermine trust in every alert.",
                     priority="core"),
            Feature(feature="Great customer support and onboarding documentation",
                     supports_core_problem="Makes it easier for new users to get started and reduces support burden.",
                     priority="optional"),
            Feature(feature="Benchmark suite comparing proxy-adapted detectors against the paper's reported label-free F1 scores",
                     supports_core_problem="Lets a team decide, in their own domain, whether the proxy adapter is trustworthy enough to replace labels — the original papers only validate in their narrow domain, so this feature makes the generalization claim checkable rather than assumed.",
                     priority="supporting"),
        ],
        feasibility_notes=(
            "The hardest part is proxy quality: a bad proxy silently produces confident-looking but wrong "
            "drift signals. The source papers manage this with domain-specific tricks (confidence filtering, "
            "geography/time-aware validation); building a domain-agnostic version that doesn't quietly degrade "
            "is unproven and is the real research risk, not the adapter plumbing."
        ),
        recurrence_signal="5 independent papers converge on proxy/pseudo-label or narrowly-scoped label-free detection as the workaround for label scarcity, but none generalizes it — a strong, consistent signal that this is a genuine unmet gap.",
        weak_features=["Great customer support and onboarding documentation"],
    ),
    dict(
        core_problem=CLUSTERS[2].tentative_core_problem,
        why_now=(
            "A 2026 industrial paper just formalized the failure-vs-domain-shift distinction as a first-class "
            "detection problem, and 2024-2026 interpretable/self-organizing detector research independently "
            "shows exactly which shift types trip up naive detectors — together they give enough structure to "
            "automate the triage step that was, until now, explicitly left to a human."
        ),
        recommended_solution=(
            "A drift-alert classifier layer that sits after any existing detector and auto-tags each alert as "
            "'benign domain evolution' or 'likely failure' using structural signals — event correlation and "
            "regime-shift structure — rather than statistical distance alone, reducing the human-in-the-loop "
            "step from every alert to only the ambiguous ones."
        ),
        features=[
            Feature(feature="Event-correlation check: cross-reference each alert timestamp against known deploy logs, data-source changes, or product-catalog updates",
                     supports_core_problem="This is the concrete signal the industrial paper's own example (new product line onboarding) shows is missing from purely statistical detectors — it's the mechanism, not a bolt-on.",
                     priority="core"),
            Feature(feature="Regime-shift classifier distinguishing 'pure re-weighting of known regimes' (benign) from 'genuinely novel regime' (likely failure), reusing the interpretable-GMM unexplained-mass signal",
                     supports_core_problem="Directly closes the gap the GMM paper documents honestly: its own detector fails exactly on pure-re-weighting drift, so this feature has to exist for the auto-triage promise to hold.",
                     priority="core"),
            Feature(feature="Only escalate to a human when the event-correlation and regime-shift signals disagree",
                     supports_core_problem="This is what actually reduces the sustained human-triage burden the industrial paper's XAI component still requires for every alert — without it, the product doesn't improve on the state of the art it's built on.",
                     priority="core"),
            Feature(feature="Beautiful, modern dashboard with customizable widgets",
                     supports_core_problem="Makes the tool more engaging and visually appealing for daily use.",
                     priority="optional"),
        ],
        feasibility_notes=(
            "The event-correlation signal only works if deploy/data-source-change events are actually logged "
            "somewhere accessible — for teams without that discipline, this degrades to the regime-shift signal "
            "alone, which the source research shows already has known blind spots (pure re-weighting). The "
            "honest limitation is that this reduces, not eliminates, false-positive triage burden."
        ),
        recurrence_signal="3 independent papers (the industrial failure-vs-shift paper, the interpretable GMM detector, and the self-organizing clustering detector) each document a version of 'naive drift detectors can't tell benign shifts from failures' — a real but smaller evidence base than the other two opportunities.",
        weak_features=["Beautiful, modern dashboard with customizable widgets"],
    ),
]


def run_dry_pipeline(
    on_stage: Callable[[int, str], None] | None = None,
) -> tuple[str, list[Opportunity]]:
    """Same shape as agent.main.run_pipeline, but backed by this fixture's canned
    gaps/clusters/drafts instead of live Anthropic calls — for exercising the API/frontend
    without a funded key."""

    def stage(i: int) -> None:
        if on_stage is not None:
            on_stage(i, STAGE_LABELS[i])

    stage(0)
    stage(1)
    print("[1/5] Retrieving real papers from arXiv/Semantic Scholar...")
    papers = retrieve(QUERIES, per_query_limit=8)
    print(f"       {len(papers)} deduped papers retrieved")

    stage(2)
    stage(3)
    # Apply the manually-authored gap extraction onto matching real Paper objects
    matched = 0
    for paper in papers:
        gaps = GAPS.get(paper.title)
        if gaps:
            paper.extracted_limitations, paper.future_work_notes = gaps
            matched += 1
    print(f"[2/5] Applied manual gap extraction to {matched}/{len(GAPS)} target papers")

    papers_by_title = {p.dedup_key(): p for p in papers}

    stage(4)
    print("[3/5] Building opportunities from manually-synthesized clusters + saturation checks...")
    opportunities = []
    for cluster, saturation, draft in zip(CLUSTERS, SATURATIONS, DRAFTS):
        # This mirrors _enforce_feature_justifications' real behavior: drop features flagged weak
        # by the critique pass, never letting it empty the list.
        kept = [f for f in draft["features"] if f.feature not in draft["weak_features"]]
        if not kept:
            kept = draft["features"]

        supporting_papers = []
        for title in cluster.supporting_paper_titles:
            matched_paper = papers_by_title.get(normalize_title(title))
            if matched_paper is None:
                print(f"       WARNING: no retrieved paper matched title {title!r}")
                continue
            finding = matched_paper.extracted_limitations + matched_paper.future_work_notes
            supporting_papers.append(SupportingPaper(
                title=matched_paper.title,
                url=matched_paper.url,
                relevant_finding=finding[0] if finding else cluster.theme_summary,
            ))

        opportunities.append(Opportunity(
            core_problem=draft["core_problem"],
            why_now=draft["why_now"],
            saturation_check=saturation,
            recommended_solution=draft["recommended_solution"],
            features=kept,
            supporting_papers=supporting_papers,
            feasibility_notes=draft["feasibility_notes"],
            recurrence_signal=draft["recurrence_signal"],
        ))
        dropped = len(draft["features"]) - len(kept)
        print(f"       Opportunity '{draft['core_problem'][:60]}...' — {len(kept)} features kept, {dropped} dropped by enforcement")

    stage(5)
    print("[4/5] Writing real JSON/Markdown output via main.py's writers...")
    import datetime
    import os
    run_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-manual"
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    _write_json(run_id, output_dir, PROBLEM_STATEMENT, opportunities)
    _write_markdown(run_id, output_dir, PROBLEM_STATEMENT, opportunities)

    print(f"[5/5] Done. Wrote {output_dir}/{run_id}.{{json,md}}")
    return run_id, opportunities


if __name__ == "__main__":
    run_dry_pipeline()
