"""Tests for the quality evaluator — focused on linter output parsing."""

import json

from src.evaluators.quality import QualityEvaluator
from src.models import Language, QualityConfig


class TestRuffParsing:

    def _make_evaluator(self, tmp_path):
        cfg = QualityConfig(weight=20, linter="ruff", max_issues=5, zero_score_at=20)
        return QualityEvaluator(cfg, Language.PYTHON, tmp_path)

    def test_parse_clean_output(self, tmp_path):
        ev = self._make_evaluator(tmp_path)
        result, issues = ev._parse_ruff_output("")
        assert result.raw_value == 0
        assert len(issues) == 0

    def test_parse_issues(self, tmp_path):
        ruff_output = json.dumps([
            {
                "code": "F401",
                "message": "os imported but unused",
                "filename": "src/solution.py",
                "location": {"row": 3, "column": 1},
            },
            {
                "code": "E501",
                "message": "Line too long (120 > 100)",
                "filename": "src/solution.py",
                "location": {"row": 17, "column": 101},
            },
            {
                "code": "W291",
                "message": "Trailing whitespace",
                "filename": "src/utils.py",
                "location": {"row": 8, "column": 15},
            },
        ])

        ev = self._make_evaluator(tmp_path)
        result, issues = ev._parse_ruff_output(ruff_output)
        assert result.raw_value == 3
        assert len(issues) == 3
        assert issues[0].code == "F401"
        assert issues[0].severity == "error"
        assert issues[1].severity == "warning"

    def test_parse_invalid_json(self, tmp_path):
        ev = self._make_evaluator(tmp_path)
        result, issues = ev._parse_ruff_output("{invalid")
        assert len(issues) == 0
        assert "parse" in result.details.lower()


class TestEslintParsing:

    def _make_evaluator(self, tmp_path):
        cfg = QualityConfig(weight=20, linter="eslint", max_issues=5, zero_score_at=20)
        return QualityEvaluator(cfg, Language.JAVASCRIPT, tmp_path)

    def test_parse_eslint_output(self, tmp_path):
        eslint_output = json.dumps([
            {
                "filePath": "src/solution.js",
                "messages": [
                    {
                        "ruleId": "no-unused-vars",
                        "severity": 2,
                        "message": "x is unused",
                        "line": 5,
                    },
                    {
                        "ruleId": "no-console",
                        "severity": 1,
                        "message": "console.log",
                        "line": 10,
                    },
                ],
            }
        ])

        ev = self._make_evaluator(tmp_path)
        result, issues = ev._parse_eslint_output(eslint_output)
        assert result.raw_value == 2
        assert issues[0].severity == "error"
        assert issues[1].severity == "warning"
