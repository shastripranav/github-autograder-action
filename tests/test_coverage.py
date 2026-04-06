"""Tests for the coverage evaluator — focused on report parsing."""

import json

from src.evaluators.coverage_eval import CoverageEvaluator
from src.models import CoverageConfig, Language


class TestCoveragePyParsing:

    def _make_evaluator(self, tmp_path):
        cfg = CoverageConfig(weight=20, minimum=60, target=90, source_dirs=["src/"])
        return CoverageEvaluator(cfg, Language.PYTHON, tmp_path)

    def test_parse_high_coverage(self, tmp_path):
        cov_data = {
            "totals": {"percent_covered": 92.5},
            "files": {
                "src/solution.py": {"summary": {"percent_covered": 95.0}},
                "src/utils.py": {"summary": {"percent_covered": 88.0}},
            },
        }
        cov_path = tmp_path / "coverage.json"
        cov_path.write_text(json.dumps(cov_data))

        ev = self._make_evaluator(tmp_path)
        result, files = ev._parse_coverage_json(cov_path)
        assert result.raw_value == 92.5
        assert len(files) == 2
        assert files[0].status == "OK"

    def test_parse_low_coverage(self, tmp_path):
        cov_data = {
            "totals": {"percent_covered": 45.0},
            "files": {
                "src/solution.py": {"summary": {"percent_covered": 45.0}},
            },
        }
        cov_path = tmp_path / "coverage.json"
        cov_path.write_text(json.dumps(cov_data))

        ev = self._make_evaluator(tmp_path)
        result, files = ev._parse_coverage_json(cov_path)
        assert result.raw_value == 45.0
        assert result.passed is False
        assert files[0].status == "Low"

    def test_missing_coverage_json(self, tmp_path):
        ev = self._make_evaluator(tmp_path)
        result, files = ev._parse_coverage_json(tmp_path / "nope.json")
        assert result.raw_value == 0
        assert len(files) == 0

    # TODO: add test for partial coverage files with mixed statuses
