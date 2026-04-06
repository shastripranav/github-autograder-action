"""Code quality evaluator — runs linters and parses issue reports."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from ..models import DimensionResult, Language, QualityConfig, QualityIssue

logger = logging.getLogger(__name__)


class QualityEvaluator:
    def __init__(self, config: QualityConfig, language: Language, workdir: Path):
        self.config = config
        self.language = language
        self.workdir = workdir

    def evaluate(self) -> tuple[DimensionResult, list[QualityIssue]]:
        if self.language == Language.PYTHON:
            return self._run_ruff()
        return self._run_eslint()

    def _run_ruff(self) -> tuple[DimensionResult, list[QualityIssue]]:
        cmd = ["ruff", "check", "--output-format=json"]
        if self.config.config:
            cmd.extend(["--config", self.config.config])
        cmd.append(str(self.workdir / "src"))

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            logger.error("ruff not found — is it installed?")
            return (
                DimensionResult(dimension="quality", details="ruff not installed"),
                [],
            )
        except subprocess.TimeoutExpired:
            return (
                DimensionResult(dimension="quality", details="ruff timed out"),
                [],
            )

        return self._parse_ruff_output(proc.stdout)

    def _parse_ruff_output(self, stdout: str) -> tuple[DimensionResult, list[QualityIssue]]:
        if not stdout.strip():
            return (
                DimensionResult(dimension="quality", raw_value=0, max_value=0, passed=True),
                [],
            )

        try:
            items = json.loads(stdout)
        except json.JSONDecodeError:
            return (
                DimensionResult(dimension="quality", details="Could not parse ruff output"),
                [],
            )

        issues = []
        for item in items:
            loc = item.get("location", {})
            issues.append(
                QualityIssue(
                    file=item.get("filename", "unknown"),
                    line=loc.get("row", 0),
                    code=item.get("code", ""),
                    message=item.get("message", ""),
                    severity="error" if item.get("code", "").startswith("F") else "warning",
                )
            )

        # severity breakdown for the summary
        errors = sum(1 for i in issues if i.severity == "error")
        warnings = len(issues) - errors
        detail_parts = []
        if errors:
            detail_parts.append(f"{errors} error{'s' if errors != 1 else ''}")
        if warnings:
            detail_parts.append(f"{warnings} warning{'s' if warnings != 1 else ''}")

        return (
            DimensionResult(
                dimension="quality",
                raw_value=float(len(issues)),
                max_value=float(self.config.zero_score_at),
                details=", ".join(detail_parts),
                passed=len(issues) <= self.config.max_issues,
            ),
            issues,
        )

    def _run_eslint(self) -> tuple[DimensionResult, list[QualityIssue]]:
        cmd = ["npx", "eslint", "--format=json", str(self.workdir / "src")]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return (
                DimensionResult(dimension="quality", details="eslint not available"),
                [],
            )

        return self._parse_eslint_output(proc.stdout)

    def _parse_eslint_output(self, stdout: str) -> tuple[DimensionResult, list[QualityIssue]]:
        """Parse eslint JSON output into issues list."""
        try:
            data = json.loads(stdout)
        except (json.JSONDecodeError, TypeError):
            return (
                DimensionResult(dimension="quality", details="Could not parse eslint output"),
                [],
            )

        issues = []
        for file_report in data:
            filepath = file_report.get("filePath", "unknown")
            for msg in file_report.get("messages", []):
                sev = "error" if msg.get("severity", 1) == 2 else "warning"
                issues.append(
                    QualityIssue(
                        file=filepath,
                        line=msg.get("line", 0),
                        code=msg.get("ruleId", ""),
                        message=msg.get("message", ""),
                        severity=sev,
                    )
                )

        return (
            DimensionResult(
                dimension="quality",
                raw_value=float(len(issues)),
                max_value=float(self.config.zero_score_at),
                passed=len(issues) <= self.config.max_issues,
            ),
            issues,
        )
