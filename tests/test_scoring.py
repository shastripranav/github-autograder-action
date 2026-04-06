"""Tests for the weighted scoring engine."""

import pytest

from src.models import (
    CoverageConfig,
    DimensionResult,
    GraderConfig,
    PerformanceConfig,
    QualityConfig,
)
from src.scoring import (
    build_scorecard,
    score_correctness,
    score_coverage,
    score_performance,
    score_quality,
)


class TestCorrectnessScoring:

    def test_perfect_score(self):
        result = DimensionResult(dimension="correctness", raw_value=10, max_value=10)
        score = score_correctness(result, weight=50)
        assert score.score == 50.0
        assert score.dimension == "Correctness"

    def test_partial_score(self):
        result = DimensionResult(dimension="correctness", raw_value=7, max_value=10)
        score = score_correctness(result, weight=50)
        assert score.score == 35.0

    def test_zero_tests(self):
        result = DimensionResult(dimension="correctness", raw_value=0, max_value=0)
        score = score_correctness(result, weight=50)
        assert score.score == 0.0

    def test_failing_score(self):
        result = DimensionResult(dimension="correctness", raw_value=2, max_value=10)
        score = score_correctness(result, weight=50)
        assert score.score == 10.0


class TestQualityScoring:

    def test_clean_code_full_marks(self):
        result = DimensionResult(dimension="quality", raw_value=0)
        cfg = QualityConfig(weight=20, max_issues=5, zero_score_at=20)
        score = score_quality(result, cfg)
        assert score.score == 20.0

    def test_at_threshold_full_marks(self):
        result = DimensionResult(dimension="quality", raw_value=5)
        cfg = QualityConfig(weight=20, max_issues=5, zero_score_at=20)
        score = score_quality(result, cfg)
        assert score.score == 20.0

    def test_linear_interpolation(self):
        result = DimensionResult(dimension="quality", raw_value=10)
        cfg = QualityConfig(weight=20, max_issues=5, zero_score_at=20)
        score = score_quality(result, cfg)
        # 20 * (1 - (10-5)/(20-5)) = 20 * (1 - 5/15) = 20 * 0.667 = 13.3
        assert score.score == pytest.approx(13.3, abs=0.1)

    def test_at_zero_threshold(self):
        result = DimensionResult(dimension="quality", raw_value=20)
        cfg = QualityConfig(weight=20, max_issues=5, zero_score_at=20)
        score = score_quality(result, cfg)
        assert score.score == 0.0

    def test_over_zero_threshold(self):
        result = DimensionResult(dimension="quality", raw_value=30)
        cfg = QualityConfig(weight=20, max_issues=5, zero_score_at=20)
        score = score_quality(result, cfg)
        assert score.score == 0.0


class TestCoverageScoring:

    def test_above_target(self):
        result = DimensionResult(dimension="coverage", raw_value=95)
        cfg = CoverageConfig(weight=20, minimum=60, target=90)
        score = score_coverage(result, cfg)
        assert score.score == 20.0

    def test_at_target(self):
        result = DimensionResult(dimension="coverage", raw_value=90)
        cfg = CoverageConfig(weight=20, minimum=60, target=90)
        score = score_coverage(result, cfg)
        assert score.score == 20.0

    def test_below_minimum(self):
        result = DimensionResult(dimension="coverage", raw_value=30)
        cfg = CoverageConfig(weight=20, minimum=60, target=90)
        score = score_coverage(result, cfg)
        assert score.score == 0.0

    def test_mid_range(self):
        result = DimensionResult(dimension="coverage", raw_value=75)
        cfg = CoverageConfig(weight=20, minimum=60, target=90)
        score = score_coverage(result, cfg)
        # 20 * (75-60)/(90-60) = 20 * 0.5 = 10.0
        assert score.score == 10.0


class TestPerformanceScoring:

    def test_disabled(self):
        result = DimensionResult(dimension="performance")
        cfg = PerformanceConfig(enabled=False)
        score = score_performance(result, cfg)
        assert score.max_score == 0.0
        assert "disabled" in score.result_summary.lower()

    def test_all_passing(self):
        result = DimensionResult(dimension="performance", raw_value=3, max_value=3)
        cfg = PerformanceConfig(weight=10, enabled=True)
        score = score_performance(result, cfg)
        assert score.score == 10.0


class TestBuildScorecard:

    def test_passing_submission_score(self, passing_correctness_result):
        """Passing submission should score ~90/100."""
        results = {
            "correctness": passing_correctness_result,
            "quality": DimensionResult(dimension="quality", raw_value=0, max_value=20),
            "coverage": DimensionResult(dimension="coverage", raw_value=92, max_value=100),
        }
        cfg = GraderConfig()
        card = build_scorecard(results, cfg)
        assert card.total_score == pytest.approx(90.0, abs=1.0)

    def test_partial_submission_score(self, partial_correctness_result):
        """Partial submission should score ~55-60."""
        results = {
            "correctness": partial_correctness_result,
            "quality": DimensionResult(dimension="quality", raw_value=8, max_value=20),
            "coverage": DimensionResult(dimension="coverage", raw_value=65, max_value=100),
        }
        cfg = GraderConfig()
        card = build_scorecard(results, cfg)
        assert 48 <= card.total_score <= 62

    def test_failing_submission_score(self, failing_correctness_result):
        """Failing submission should score ~15."""
        results = {
            "correctness": failing_correctness_result,
            "quality": DimensionResult(dimension="quality", raw_value=15, max_value=20),
            "coverage": DimensionResult(dimension="coverage", raw_value=30, max_value=100),
        }
        cfg = GraderConfig()
        card = build_scorecard(results, cfg)
        assert 10 <= card.total_score <= 20
