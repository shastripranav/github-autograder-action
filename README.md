# GitHub Actions Auto-Grader

[![CI](https://github.com/shastripranav/github-autograder-action/actions/workflows/ci.yml/badge.svg)](https://github.com/shastripranav/github-autograder-action/actions/workflows/ci.yml)

Multi-dimensional code assessment engine packaged as a GitHub Action. Evaluates student submissions on **correctness**, **code quality**, **test coverage**, and **performance** — generating weighted scorecards as PR comments.

> Drop a config file and a workflow into any assignment repo and it works. No infrastructure required.

## Architecture

```
Student pushes code → GitHub Actions triggers
              │
    ┌─────────┼─────────────┐
    ▼         ▼             ▼
┌────────┐ ┌────────┐ ┌──────────┐
│Correct-│ │ Code   │ │ Coverage │
│  ness  │ │Quality │ │ Analysis │
│ pytest │ │  ruff  │ │coverage  │
│  jest  │ │ eslint │ │ istanbul │
└───┬────┘ └───┬────┘ └────┬─────┘
    └──────────┼────────────┘
               ▼
     ┌──────────────────┐
     │ Score Aggregator  │
     │ (weighted scores) │
     └────────┬─────────┘
              ▼
     ┌──────────────────┐
     │  Report Output   │
     │ PR Comment + JSON│
     └──────────────────┘
```

## Quick Start

### 1. Add to your assignment repo

```yaml
# .github/workflows/grade.yml
name: Auto-Grade
on: [push, pull_request]

jobs:
  grade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Grade Submission
        uses: shastripranav/github-autograder@v1
        with:
          config: grader-config.yml
          github-token: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Add a grading config

```yaml
# grader-config.yml
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
```

### 3. Students submit code, get instant feedback

The grader posts a scorecard as a PR comment:

```
## Auto-Grader Report

| Dimension     | Result              | Weight | Score     |
|---------------|---------------------|--------|-----------|
| Correctness   | 8/10 tests passing  | 50%    | 40.0/50   |
| Code Quality  | 3 issues            | 20%    | 17.3/20   |
| Test Coverage | 78% line coverage   | 20%    | 12.0/20   |
| Performance   | N/A (disabled)      | 10%    | —         |
| **Total**     |                     |        | **69.3/100** |
```

## Configuration Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `language` | `python` \| `javascript` | `python` | Submission language |
| `correctness.weight` | int | 50 | Weight for test results |
| `correctness.framework` | `pytest` \| `jest` | `pytest` | Test framework |
| `correctness.timeout` | int | 30 | Seconds per test |
| `quality.weight` | int | 20 | Weight for lint quality |
| `quality.linter` | `ruff` \| `eslint` | `ruff` | Linter to use |
| `quality.max_issues` | int | 5 | Issues threshold for full marks |
| `quality.zero_score_at` | int | 20 | Issues threshold for zero marks |
| `coverage.weight` | int | 20 | Weight for coverage score |
| `coverage.minimum` | float | 60 | Below this = 0 points |
| `coverage.target` | float | 90 | At or above = full points |
| `performance.enabled` | bool | false | Enable benchmark scoring |

## Scoring Formulas

**Correctness**: `score = (tests_passed / total_tests) * weight`

**Quality**: Linear interpolation between `max_issues` (full marks) and `zero_score_at` (zero marks)

**Coverage**: Linear interpolation between `minimum` (0 points) and `target` (full marks)

**Performance**: `score = (benchmarks_passed / total_benchmarks) * weight`

## Development

```bash
# install
pip install -e ".[dev,grading]"

# test
pytest

# lint
ruff check src/ tests/ --exclude tests/fixtures
```

## Test Fixtures

Three reference submissions for the "k most frequent elements" problem:

| Fixture | Tests Passing | Expected Score |
|---------|--------------|----------------|
| `passing_submission` | 10/10 | ~90/100 |
| `partial_submission` | 7/10 | ~58/100 |
| `failing_submission` | 2/10 | ~17/100 |

## License

MIT
