"""Shared fixtures for the grader test suite."""

from pathlib import Path

import pytest

from src.models import (
    DimensionResult,
    GraderConfig,
    TestFailure,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def passing_dir():
    return FIXTURES_DIR / "passing_submission"


@pytest.fixture
def partial_dir():
    return FIXTURES_DIR / "partial_submission"


@pytest.fixture
def failing_dir():
    return FIXTURES_DIR / "failing_submission"


@pytest.fixture
def default_config():
    return GraderConfig()


@pytest.fixture
def sample_config(tmp_path):
    """Write a grader-config.yml to a temp dir and return the path."""
    cfg_content = """
language: python
correctness:
  weight: 50
  framework: pytest
  test_dir: tests/
  timeout: 30
quality:
  weight: 20
  linter: ruff
  max_issues: 5
  zero_score_at: 20
coverage:
  weight: 20
  tool: coverage
  minimum: 60
  target: 90
  source_dirs:
    - src/
performance:
  weight: 10
  enabled: false
"""
    p = tmp_path / "grader-config.yml"
    p.write_text(cfg_content)
    return p


@pytest.fixture
def passing_correctness_result():
    return DimensionResult(
        dimension="correctness",
        raw_value=10.0,
        max_value=10.0,
        details="10/10 tests passed",
        passed=True,
    )


@pytest.fixture
def partial_correctness_result():
    return DimensionResult(
        dimension="correctness",
        raw_value=7.0,
        max_value=10.0,
        details="7/10 tests passed",
        failures=[
            TestFailure(test_name="test_empty_list", message="assert None == []"),
            TestFailure(test_name="test_k_exceeds_unique", message="IndexError"),
            TestFailure(test_name="test_k_zero", message="assert [1, 2, 3] == []"),
        ],
        passed=False,
    )


@pytest.fixture
def failing_correctness_result():
    return DimensionResult(
        dimension="correctness",
        raw_value=2.0,
        max_value=10.0,
        details="2/10 tests passed",
        passed=False,
    )
