"""Pydantic models for grader configuration, scores, and reports."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"


class CorrectnessConfig(BaseModel):
    weight: int = 50
    framework: str = "pytest"
    test_dir: str = "tests/"
    timeout: int = 30

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        allowed = {"pytest", "jest"}
        if v not in allowed:
            raise ValueError(f"framework must be one of {allowed}")
        return v


class QualityConfig(BaseModel):
    weight: int = 20
    linter: str = "ruff"
    config: str | None = None
    max_issues: int = 5
    zero_score_at: int = 20

    @field_validator("linter")
    @classmethod
    def validate_linter(cls, v: str) -> str:
        allowed = {"ruff", "eslint"}
        if v not in allowed:
            raise ValueError(f"linter must be one of {allowed}")
        return v


class CoverageConfig(BaseModel):
    weight: int = 20
    tool: str = "coverage"
    minimum: float = 60.0
    target: float = 90.0
    source_dirs: list[str] = Field(default_factory=lambda: ["src/"])


class BenchmarkConfig(BaseModel):
    name: str
    command: str
    max_time: float = 2.0


class PerformanceConfig(BaseModel):
    weight: int = 10
    enabled: bool = False
    benchmarks: list[BenchmarkConfig] = Field(default_factory=list)


class GraderConfig(BaseModel):
    """Top-level grading configuration parsed from grader-config.yml."""

    language: Language = Language.PYTHON
    correctness: CorrectnessConfig = Field(default_factory=CorrectnessConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    coverage: CoverageConfig = Field(default_factory=CoverageConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    def total_weight(self) -> int:
        weights = self.correctness.weight + self.quality.weight + self.coverage.weight
        if self.performance.enabled:
            weights += self.performance.weight
        return weights


# --- Score / result models ---


class TestFailure(BaseModel):
    __test__ = False  # prevent pytest from collecting this as a test class

    test_name: str
    message: str = ""


class DimensionResult(BaseModel):
    """Raw output from a single evaluator before scoring."""

    dimension: str
    raw_value: float = 0.0
    max_value: float = 0.0
    details: str = ""
    failures: list[TestFailure] = Field(default_factory=list)
    passed: bool = True


class QualityIssue(BaseModel):
    file: str
    line: int = 0
    code: str = ""
    message: str = ""
    severity: str = "warning"


class CoverageFile(BaseModel):
    file: str
    coverage_pct: float
    status: str = "OK"


class DimensionScore(BaseModel):
    dimension: str
    result_summary: str
    weight: int
    score: float
    max_score: float

    @property
    def pct(self) -> float:
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0.0


class Scorecard(BaseModel):
    scores: list[DimensionScore] = Field(default_factory=list)
    total_score: float = 0.0
    max_possible: float = 100.0

    quality_issues: list[QualityIssue] = Field(default_factory=list)
    coverage_files: list[CoverageFile] = Field(default_factory=list)
    test_failures: list[TestFailure] = Field(default_factory=list)

    def compute_total(self) -> None:
        self.total_score = sum(s.score for s in self.scores)
        self.max_possible = sum(s.max_score for s in self.scores)


class GraderReport(BaseModel):
    """Final output — wraps scorecard with metadata for serialization."""

    scorecard: Scorecard
    language: str = "python"
    config_path: str = "grader-config.yml"
    markdown: str = ""
