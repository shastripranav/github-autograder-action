"""Tests for the Markdown and JSON report generator."""

import json

from src.models import (
    CoverageFile,
    DimensionScore,
    QualityIssue,
    Scorecard,
    TestFailure,
)
from src.reporter import render_json, render_markdown


def _make_scorecard() -> Scorecard:
    card = Scorecard(
        scores=[
            DimensionScore(
                dimension="Correctness",
                result_summary="8/10 tests passing",
                weight=50,
                score=40.0,
                max_score=50.0,
            ),
            DimensionScore(
                dimension="Code Quality",
                result_summary="3 issues",
                weight=20,
                score=17.3,
                max_score=20.0,
            ),
            DimensionScore(
                dimension="Test Coverage",
                result_summary="78% line coverage",
                weight=20,
                score=12.0,
                max_score=20.0,
            ),
            DimensionScore(
                dimension="Performance",
                result_summary="N/A (disabled)",
                weight=10,
                score=0.0,
                max_score=0.0,
            ),
        ],
        test_failures=[
            TestFailure(test_name="test_edge_case", message="AssertionError: expected []"),
        ],
        quality_issues=[
            QualityIssue(
                file="src/solution.py", line=42, code="F401",
                message="os imported but unused",
            ),
        ],
        coverage_files=[
            CoverageFile(file="src/solution.py", coverage_pct=85.0, status="OK"),
            CoverageFile(file="src/utils.py", coverage_pct=64.0, status="Warning"),
        ],
    )
    card.compute_total()
    return card


class TestMarkdownReport:

    def test_contains_table_header(self):
        card = _make_scorecard()
        md = render_markdown(card)
        assert "| Dimension |" in md

    def test_contains_total_score(self):
        card = _make_scorecard()
        md = render_markdown(card)
        assert "69.3" in md

    def test_contains_failing_tests_section(self):
        card = _make_scorecard()
        md = render_markdown(card)
        assert "Failing Tests" in md
        assert "test_edge_case" in md

    def test_contains_quality_issues(self):
        card = _make_scorecard()
        md = render_markdown(card)
        assert "F401" in md

    def test_contains_coverage_table(self):
        card = _make_scorecard()
        md = render_markdown(card)
        assert "src/solution.py" in md
        assert "85%" in md


class TestJsonReport:

    def test_valid_json(self):
        card = _make_scorecard()
        raw = render_json(card)
        data = json.loads(raw)
        assert "total_score" in data

    def test_dimensions_present(self):
        card = _make_scorecard()
        data = json.loads(render_json(card))
        assert len(data["dimensions"]) == 4

    def test_failing_tests_in_json(self):
        card = _make_scorecard()
        data = json.loads(render_json(card))
        assert len(data["failing_tests"]) == 1
        assert data["failing_tests"][0]["test"] == "test_edge_case"

    # TODO: add test for report with no failures (empty sections)
