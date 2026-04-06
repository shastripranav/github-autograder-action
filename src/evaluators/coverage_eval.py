"""Coverage evaluator — measures test coverage via coverage.py or istanbul/c8."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from ..models import CoverageConfig, CoverageFile, DimensionResult, Language

logger = logging.getLogger(__name__)


class CoverageEvaluator:
    def __init__(self, config: CoverageConfig, language: Language, workdir: Path):
        self.config = config
        self.language = language
        self.workdir = workdir

    def evaluate(self) -> tuple[DimensionResult, list[CoverageFile]]:
        if self.language == Language.PYTHON:
            return self._run_coverage_py()
        return self._run_c8()

    def _run_coverage_py(self) -> tuple[DimensionResult, list[CoverageFile]]:
        source_args = []
        for d in self.config.source_dirs:
            source_args.extend(["--cov", str(self.workdir / d)])

        cmd = [
            sys.executable, "-m", "pytest",
            str(self.workdir / "tests"),
            *source_args,
            "--cov-report=json",
            "-q", "--no-header",
        ]

        cov_json = self.workdir / "coverage.json"

        try:
            subprocess.run(
                cmd, cwd=str(self.workdir),
                capture_output=True, text=True, timeout=120,
            )
        except subprocess.TimeoutExpired:
            return (
                DimensionResult(dimension="coverage", details="Coverage run timed out"),
                [],
            )
        except FileNotFoundError:
            return (
                DimensionResult(dimension="coverage", details="pytest-cov not installed"),
                [],
            )

        return self._parse_coverage_json(cov_json)

    def _parse_coverage_json(self, path: Path) -> tuple[DimensionResult, list[CoverageFile]]:
        if not path.exists():
            return (
                DimensionResult(dimension="coverage", details="No coverage.json generated"),
                [],
            )

        data = json.loads(path.read_text())
        totals = data.get("totals", {})
        total_pct = totals.get("percent_covered", 0.0)

        files = []
        for fname, fdata in data.get("files", {}).items():
            pct = fdata.get("summary", {}).get("percent_covered", 0.0)
            if pct >= self.config.target:
                status = "OK"
            elif pct >= self.config.minimum:
                status = "Warning"
            else:
                status = "Low"
            files.append(CoverageFile(file=fname, coverage_pct=round(pct, 1), status=status))

        return (
            DimensionResult(
                dimension="coverage",
                raw_value=round(total_pct, 1),
                max_value=100.0,
                details=f"{total_pct:.0f}% total coverage",
                passed=total_pct >= self.config.minimum,
            ),
            files,
        )

    def _run_c8(self) -> tuple[DimensionResult, list[CoverageFile]]:
        """Run c8/istanbul for JS coverage — similar pattern to coverage.py."""
        report_path = self.workdir / "coverage" / "coverage-summary.json"
        cmd = [
            "npx", "c8",
            "--reporter=json-summary",
            "--report-dir", str(self.workdir / "coverage"),
            "npx", "jest", "--forceExit",
        ]

        try:
            subprocess.run(cmd, cwd=str(self.workdir), capture_output=True, text=True, timeout=120)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return (
                DimensionResult(dimension="coverage", details="c8 not available"),
                [],
            )

        return self._parse_c8_output(report_path)

    def _parse_c8_output(self, path: Path) -> tuple[DimensionResult, list[CoverageFile]]:
        if not path.exists():
            return (
                DimensionResult(dimension="coverage", details="No c8 report generated"),
                [],
            )

        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            return (
                DimensionResult(dimension="coverage", details="Could not parse c8 output"),
                [],
            )

        total_info = data.get("total", {}).get("lines", {})
        total_pct = total_info.get("pct", 0.0)

        # FIXME: c8 summary format doesn't include per-file breakdown in all versions
        files = []
        for fname, fdata in data.items():
            if fname == "total":
                continue
            pct = fdata.get("lines", {}).get("pct", 0.0)
            status = "OK" if pct >= self.config.target else "Warning"
            files.append(CoverageFile(file=fname, coverage_pct=round(pct, 1), status=status))

        return (
            DimensionResult(
                dimension="coverage",
                raw_value=round(total_pct, 1),
                max_value=100.0,
                details=f"{total_pct:.0f}% total coverage",
                passed=total_pct >= self.config.minimum,
            ),
            files,
        )
