"""Main grading orchestrator — ties evaluators, scoring, and reporting together."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from .config import load_config_or_defaults
from .evaluators.correctness import CorrectnessEvaluator
from .evaluators.coverage_eval import CoverageEvaluator
from .evaluators.performance import PerformanceEvaluator
from .evaluators.quality import QualityEvaluator
from .github_client import GitHubClient
from .models import DimensionResult, GraderConfig
from .reporter import build_report, render_json, write_scorecard_json
from .scoring import build_scorecard

logger = logging.getLogger(__name__)


class Grader:
    def __init__(self, config: GraderConfig, workdir: Path):
        self.config = config
        self.workdir = workdir

    def run(self) -> dict:
        """Execute all evaluators and produce the final scorecard."""
        results: dict[str, DimensionResult] = {}

        # correctness
        ce = CorrectnessEvaluator(self.config.correctness, self.config.language, self.workdir)
        results["correctness"] = ce.evaluate()

        # quality
        qe = QualityEvaluator(self.config.quality, self.config.language, self.workdir)
        quality_result, quality_issues = qe.evaluate()
        results["quality"] = quality_result

        # coverage
        cov = CoverageEvaluator(self.config.coverage, self.config.language, self.workdir)
        cov_result, cov_files = cov.evaluate()
        results["coverage"] = cov_result

        # performance (only if enabled)
        if self.config.performance.enabled:
            pe = PerformanceEvaluator(self.config.performance, self.workdir)
            results["performance"] = pe.evaluate()

        # build scorecard
        scorecard = build_scorecard(results, self.config)
        scorecard.test_failures = results["correctness"].failures
        scorecard.quality_issues = quality_issues
        scorecard.coverage_files = cov_files

        report = build_report(
            scorecard,
            language=self.config.language.value,
            config_path=str(self.workdir / "grader-config.yml"),
        )

        return {
            "scorecard": scorecard,
            "report": report,
            "json": render_json(scorecard),
        }


def main():
    """CLI entrypoint — used by the Docker action."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    config_path = sys.argv[1] if len(sys.argv) > 1 else "grader-config.yml"
    github_token = sys.argv[2] if len(sys.argv) > 2 else None
    post_comment = (sys.argv[3] if len(sys.argv) > 3 else "true").lower() == "true"

    workdir = Path.cwd()
    cfg = load_config_or_defaults(config_path)

    grader = Grader(cfg, workdir)
    output = grader.run()

    scorecard = output["scorecard"]
    report = output["report"]

    # write JSON artifact
    write_scorecard_json(scorecard)
    logger.info("Scorecard written to scorecard.json")

    # GitHub Actions integration
    gh = GitHubClient(token=github_token)
    gh.write_job_summary(report.markdown)
    gh.set_output("total-score", str(scorecard.total_score))
    import json
    minified_json = json.dumps(json.loads(output["json"]))
    gh.set_output("scorecard-json", minified_json)

    if post_comment:
        gh.post_pr_comment(report.markdown)

    print(f"\nFinal score: {scorecard.total_score}/{scorecard.max_possible}")


if __name__ == "__main__":
    main()
