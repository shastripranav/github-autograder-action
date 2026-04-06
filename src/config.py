"""Load and validate grader-config.yml files."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from .models import GraderConfig

logger = logging.getLogger(__name__)


def load_config(config_path: str | Path) -> GraderConfig:
    """Parse a grader-config.yml and return a validated GraderConfig."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    try:
        cfg = GraderConfig.model_validate(data)
    except ValidationError as exc:
        # surface pydantic errors as a readable string
        raise ValueError(f"Config validation failed:\n{exc}") from exc

    _warn_weight_mismatch(cfg)
    return cfg


def _warn_weight_mismatch(cfg: GraderConfig):
    total = cfg.total_weight()
    if total != 100:
        logger.warning(
            "Dimension weights sum to %d (expected 100). Scores will still be "
            "computed against configured weights.",
            total,
        )


def load_config_or_defaults(config_path: str | Path | None = None) -> GraderConfig:
    if config_path is None:
        return GraderConfig()
    return load_config(config_path)
