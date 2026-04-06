"""Correctness evaluator — runs test suites and parses results."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from ..models import CorrectnessConfig, DimensionResult, Language, TestFailure

logger = logging.getLogger(__name__)


class CorrectnessEvaluator:
    def __init__(self, config: CorrectnessConfig, language: Language, workdir: Path):
        self.config = config
        self.language = language
        self.workdir = workdir

    def evaluate(self) -> DimensionResult:
        if self.language == Language.PYTHON:
            return self._run_pytest()
        return self._run_jest()

    def _run_pytest(self) -> DimensionResult:
        """Run pytest with JSON report and parse results."""
        report_path = self.workdir / ".report.json"
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.workdir / self.config.test_dir),
            f"--timeout={self.config.timeout}",
            "--tb=short",
            "--json-report",
            f"--json-report-file={report_path}",
            "-q",
        ]

        try:
            subprocess.run(
                cmd,
                cwd=str(self.workdir),
                capture_output=True,
                text=True,
                timeout=self.config.timeout * 10,
            )
        except subprocess.TimeoutExpired:
            logger.error("pytest timed out after %ds", self.config.timeout * 10)
            return DimensionResult(
                dimension="correctness",
                details="Test suite timed out",
                passed=False,
            )

        return self._parse_pytest_report(report_path)

    def _parse_pytest_report(self, report_path: Path) -> DimensionResult:
        if not report_path.exists():
            return DimensionResult(
                dimension="correctness",
                details="No test report generated — pytest may have crashed",
                passed=False,
            )

        data = json.loads(report_path.read_text())
        summary = data.get("summary", {})
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)

        failures = []
        for test in data.get("tests", []):
            if test.get("outcome") != "passed":
                msg = ""
                call_info = test.get("call", {})
                if call_info:
                    # grab just the crash message, not the full traceback
                    crash = call_info.get("crash", {})
                    msg = crash.get("message", call_info.get("longrepr", ""))
                failures.append(TestFailure(test_name=test["nodeid"], message=str(msg)[:200]))

        return DimensionResult(
            dimension="correctness",
            raw_value=float(passed),
            max_value=float(total),
            details=f"{passed}/{total} tests passed",
            failures=failures,
            passed=(passed == total),
        )

    def _run_jest(self) -> DimensionResult:
        """Run jest with JSON output and parse results."""
        cmd = [
            "npx", "jest",
            "--json",
            "--testPathPattern", self.config.test_dir,
            "--forceExit",
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.workdir),
                capture_output=True,
                text=True,
                timeout=self.config.timeout * 10,
            )
        except subprocess.TimeoutExpired:
            return DimensionResult(
                dimension="correctness",
                details="Jest timed out",
                passed=False,
            )

        return self._parse_jest_output(proc.stdout)

    def _parse_jest_output(self, stdout: str) -> DimensionResult:
        try:
            data = json.loads(stdout)
        except (json.JSONDecodeError, TypeError):
            return DimensionResult(
                dimension="correctness",
                details="Failed to parse jest JSON output",
                passed=False,
            )

        total = data.get("numTotalTests", 0)
        passed = data.get("numPassedTests", 0)

        failures = []
        for suite in data.get("testResults", []):
            for test in suite.get("assertionResults", []):
                if test.get("status") != "passed":
                    msg = " ".join(test.get("failureMessages", []))[:200]
                    failures.append(TestFailure(test_name=test["fullName"], message=msg))

        return DimensionResult(
            dimension="correctness",
            raw_value=float(passed),
            max_value=float(total),
            details=f"{passed}/{total} tests passed",
            failures=failures,
            passed=(passed == total),
        )
