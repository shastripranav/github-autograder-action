"""Tests for the correctness evaluator — focused on output parsing."""

import json

from src.evaluators.correctness import CorrectnessEvaluator
from src.models import CorrectnessConfig, Language


class TestPytestParsing:

    def _make_evaluator(self, tmp_path):
        cfg = CorrectnessConfig(framework="pytest", test_dir="tests/", timeout=30)
        return CorrectnessEvaluator(cfg, Language.PYTHON, tmp_path)

    def test_parse_full_pass(self, tmp_path):
        report = {
            "summary": {"total": 10, "passed": 10},
            "tests": [
                {"nodeid": f"test_{i}", "outcome": "passed"} for i in range(10)
            ],
        }
        report_path = tmp_path / ".report.json"
        report_path.write_text(json.dumps(report))

        ev = self._make_evaluator(tmp_path)
        result = ev._parse_pytest_report(report_path)
        assert result.raw_value == 10.0
        assert result.max_value == 10.0
        assert result.passed is True
        assert len(result.failures) == 0

    def test_parse_partial_failures(self, tmp_path):
        report = {
            "summary": {"total": 10, "passed": 7, "failed": 3},
            "tests": [
                {"nodeid": f"test_{i}", "outcome": "passed"} for i in range(7)
            ] + [
                {
                    "nodeid": "test_edge",
                    "outcome": "failed",
                    "call": {"crash": {"message": "AssertionError"}},
                },
                {
                    "nodeid": "test_null",
                    "outcome": "failed",
                    "call": {"crash": {"message": "TypeError"}},
                },
                {
                    "nodeid": "test_timeout",
                    "outcome": "failed",
                    "call": {"crash": {"message": "TimeoutError"}},
                },
            ],
        }
        report_path = tmp_path / ".report.json"
        report_path.write_text(json.dumps(report))

        ev = self._make_evaluator(tmp_path)
        result = ev._parse_pytest_report(report_path)
        assert result.raw_value == 7.0
        assert result.max_value == 10.0
        assert len(result.failures) == 3

    def test_missing_report(self, tmp_path):
        ev = self._make_evaluator(tmp_path)
        result = ev._parse_pytest_report(tmp_path / "missing.json")
        assert result.raw_value == 0.0
        assert "crashed" in result.details.lower() or "no test report" in result.details.lower()


class TestJestParsing:

    def _make_evaluator(self, tmp_path):
        cfg = CorrectnessConfig(framework="jest", test_dir="tests/", timeout=30)
        return CorrectnessEvaluator(cfg, Language.JAVASCRIPT, tmp_path)

    def test_parse_jest_all_pass(self, tmp_path):
        jest_output = json.dumps({
            "numTotalTests": 5,
            "numPassedTests": 5,
            "testResults": [
                {
                    "assertionResults": [
                        {"fullName": f"test {i}", "status": "passed"} for i in range(5)
                    ]
                }
            ],
        })
        ev = self._make_evaluator(tmp_path)
        result = ev._parse_jest_output(jest_output)
        assert result.raw_value == 5.0
        assert result.passed is True

    def test_parse_invalid_json(self, tmp_path):
        ev = self._make_evaluator(tmp_path)
        result = ev._parse_jest_output("not json at all")
        assert result.raw_value == 0.0
        assert "parse" in result.details.lower()
