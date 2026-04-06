"""Performance evaluator — runs benchmark commands and checks timing thresholds."""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from ..models import DimensionResult, PerformanceConfig

logger = logging.getLogger(__name__)


class PerformanceEvaluator:
    def __init__(self, config: PerformanceConfig, workdir: Path):
        self.config = config
        self.workdir = workdir

    def evaluate(self) -> DimensionResult:
        if not self.config.enabled:
            return DimensionResult(
                dimension="performance",
                details="Performance benchmarks disabled",
            )

        if not self.config.benchmarks:
            return DimensionResult(
                dimension="performance",
                details="No benchmarks configured",
            )

        passed = 0
        total = len(self.config.benchmarks)

        for bench in self.config.benchmarks:
            ok = self._run_benchmark(bench.command, bench.max_time)
            if ok:
                passed += 1

        return DimensionResult(
            dimension="performance",
            raw_value=float(passed),
            max_value=float(total),
            details=f"{passed}/{total} benchmarks within time limits",
            passed=(passed == total),
        )

    def _run_benchmark(self, command: str, max_time: float) -> bool:
        start = time.monotonic()
        try:
            proc = subprocess.run(
                command.split(),
                cwd=str(self.workdir),
                capture_output=True,
                text=True,
                timeout=max_time * 3,  # generous timeout, we measure wall time separately
            )
        except subprocess.TimeoutExpired:
            logger.warning("Benchmark timed out: %s", command)
            return False
        except FileNotFoundError:
            logger.warning("Benchmark command not found: %s", command)
            return False

        elapsed = time.monotonic() - start

        if proc.returncode != 0:
            return False

        return elapsed <= max_time
