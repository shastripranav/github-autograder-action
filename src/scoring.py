"""Weighted score calculation engine.

Implements the scoring formulas for each grading dimension:
correctness, quality, coverage, and performance.
"""

from __future__ import annotations

from .models import (
    CoverageConfig,
    DimensionResult,
    DimensionScore,
    GraderConfig,
    PerformanceConfig,
    QualityConfig,
    Scorecard,
)


def score_correctness(result: DimensionResult, weight: int) -> DimensionScore:
    if result.max_value == 0:
        ratio = 0.0
    else:
        ratio = result.raw_value / result.max_value

    return DimensionScore(
        dimension="Correctness",
        result_summary=f"{int(result.raw_value)}/{int(result.max_value)} tests passing",
        weight=weight,
        score=round(ratio * weight, 1),
        max_score=float(weight),
    )


def score_quality(result: DimensionResult, cfg: QualityConfig) -> DimensionScore:
    """Linear interpolation between max_issues (full marks) and zero_score_at (zero)."""
    issues = int(result.raw_value)

    if issues <= cfg.max_issues:
        score = float(cfg.weight)
    elif issues >= cfg.zero_score_at:
        score = 0.0
    else:
        # linear dropoff between thresholds
        score = cfg.weight * (1 - (issues - cfg.max_issues) / (cfg.zero_score_at - cfg.max_issues))
        score = round(score, 1)

    summary = f"{issues} issue{'s' if issues != 1 else ''}"
    if result.details:
        summary += f" ({result.details})"

    return DimensionScore(
        dimension="Code Quality",
        result_summary=summary,
        weight=cfg.weight,
        score=score,
        max_score=float(cfg.weight),
    )


def score_coverage(result: DimensionResult, cfg: CoverageConfig) -> DimensionScore:
    pct = result.raw_value

    if pct < cfg.minimum:
        score = 0.0
    elif pct >= cfg.target:
        score = float(cfg.weight)
    else:
        score = cfg.weight * (pct - cfg.minimum) / (cfg.target - cfg.minimum)
        score = round(score, 1)

    return DimensionScore(
        dimension="Test Coverage",
        result_summary=f"{pct:.0f}% line coverage",
        weight=cfg.weight,
        score=score,
        max_score=float(cfg.weight),
    )


def score_performance(result: DimensionResult, cfg: PerformanceConfig) -> DimensionScore:
    if not cfg.enabled:
        return DimensionScore(
            dimension="Performance",
            result_summary="N/A (disabled)",
            weight=cfg.weight,
            score=0.0,
            max_score=0.0,  # doesn't count toward total when disabled
        )

    total = result.max_value
    passed = result.raw_value
    if total == 0:
        ratio = 0.0
    else:
        ratio = passed / total

    return DimensionScore(
        dimension="Performance",
        result_summary=f"{int(passed)}/{int(total)} benchmarks passing",
        weight=cfg.weight,
        score=round(ratio * cfg.weight, 1),
        max_score=float(cfg.weight),
    )


def build_scorecard(
    results: dict[str, DimensionResult],
    config: GraderConfig,
) -> Scorecard:
    """Aggregate dimension results into a final scorecard."""
    scores = []

    if "correctness" in results:
        scores.append(score_correctness(results["correctness"], config.correctness.weight))

    if "quality" in results:
        scores.append(score_quality(results["quality"], config.quality))

    if "coverage" in results:
        scores.append(score_coverage(results["coverage"], config.coverage))

    perf = results.get("performance")
    scores.append(
        score_performance(
            perf or DimensionResult(dimension="performance"),
            config.performance,
        )
    )

    card = Scorecard(scores=scores)
    card.compute_total()
    return card
