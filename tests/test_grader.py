"""Tests for the main grader orchestrator and config loading."""

import pytest
import yaml

from src.config import load_config, load_config_or_defaults
from src.models import Language


class TestConfigLoader:

    def test_valid_yaml_parses(self, sample_config):
        cfg = load_config(sample_config)
        assert cfg.language == Language.PYTHON
        assert cfg.correctness.weight == 50

    def test_defaults_applied(self):
        cfg = load_config_or_defaults(None)
        assert cfg.correctness.weight == 50
        assert cfg.quality.max_issues == 5
        assert cfg.coverage.minimum == 60.0

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yml")

    def test_invalid_yaml_raises(self, tmp_path):
        bad = tmp_path / "bad.yml"
        bad.write_text(": : :\n  - [invalid yaml here")
        with pytest.raises(ValueError, match="Invalid YAML"):
            load_config(bad)

    def test_invalid_framework_raises(self, tmp_path):
        bad_cfg = tmp_path / "bad-framework.yml"
        bad_cfg.write_text(yaml.dump({"correctness": {"framework": "mocha"}}))
        with pytest.raises(ValueError, match="Config validation"):
            load_config(bad_cfg)

    def test_javascript_config(self, tmp_path):
        js_cfg = tmp_path / "js.yml"
        js_cfg.write_text(yaml.dump({
            "language": "javascript",
            "correctness": {"framework": "jest"},
            "quality": {"linter": "eslint"},
        }))
        cfg = load_config(js_cfg)
        assert cfg.language == Language.JAVASCRIPT
        assert cfg.correctness.framework == "jest"

    def test_partial_config_uses_defaults(self, tmp_path):
        partial = tmp_path / "partial.yml"
        partial.write_text(yaml.dump({"language": "python"}))
        cfg = load_config(partial)
        assert cfg.correctness.weight == 50
        assert cfg.performance.enabled is False

    def test_weight_sum(self, sample_config):
        cfg = load_config(sample_config)
        # performance disabled, so total = 50+20+20 = 90
        assert cfg.total_weight() == 90
