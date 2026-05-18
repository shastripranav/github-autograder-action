# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-04-27

### Added

- Four-dimensional code grading: correctness (test execution), code quality (linting), test coverage, and performance benchmarks
- Multi-language support: Python (pytest, ruff, coverage) and JavaScript (jest, eslint, c8)
- Per-assignment configurable weighting via `grader-config.yml`
- Pydantic-validated configuration that catches misconfigurations before grading runs
- Weighted scorecard generation with categorized breakdown
- Jinja2-based Markdown report rendering for human-readable feedback
- Automatic PR comment integration posting the scorecard
- GitHub Actions step summary and `GITHUB_OUTPUT` integration (`total-score` and `scorecard-json` outputs)
- Docker-based execution for consistent grading environment across runners
- Marketplace branding (`check-circle` icon and `green` color) on `action.yml`
- Test fixtures covering passing, partial, and failing student submissions
