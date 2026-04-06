"""Report generator — renders Markdown and JSON from scorecard data."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .models import GraderReport, Scorecard

# template lives next to the package root
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def render_markdown(scorecard: Scorecard, template_dir: Path | None = None) -> str:
    tpl_dir = template_dir or _TEMPLATE_DIR
    env = Environment(
        loader=FileSystemLoader(str(tpl_dir)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("report.md.jinja2")
    return template.render(scorecard=scorecard)


def render_json(scorecard: Scorecard) -> str:
    data = {
        "total_score": scorecard.total_score,
        "max_possible": scorecard.max_possible,
        "dimensions": [
            {
                "dimension": s.dimension,
                "result": s.result_summary,
                "weight": s.weight,
                "score": s.score,
                "max_score": s.max_score,
            }
            for s in scorecard.scores
        ],
    }

    if scorecard.test_failures:
        data["failing_tests"] = [
            {"test": f.test_name, "message": f.message}
            for f in scorecard.test_failures
        ]

    if scorecard.quality_issues:
        data["quality_issues"] = [
            {"file": i.file, "line": i.line, "code": i.code, "message": i.message}
            for i in scorecard.quality_issues
        ]

    if scorecard.coverage_files:
        data["coverage_files"] = [
            {"file": f.file, "coverage": f.coverage_pct, "status": f.status}
            for f in scorecard.coverage_files
        ]

    return json.dumps(data, indent=2)


def build_report(
    scorecard: Scorecard,
    language: str = "python",
    config_path: str = "grader-config.yml",
) -> GraderReport:
    md = render_markdown(scorecard)
    return GraderReport(
        scorecard=scorecard,
        language=language,
        config_path=config_path,
        markdown=md,
    )


def write_scorecard_json(scorecard: Scorecard, output_path: str | Path = "scorecard.json"):
    """Dump scorecard to a JSON file for artifact upload."""
    path = Path(output_path)
    path.write_text(render_json(scorecard), encoding="utf-8")
