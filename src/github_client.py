"""GitHub API client for posting PR comments and writing job summaries."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubClient:
    """Lightweight client for the GitHub REST API — just the endpoints we need."""

    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.repo = os.environ.get("GITHUB_REPOSITORY", "")
        self._headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def post_pr_comment(self, body: str, pr_number: int | None = None):
        """Post a comment on the current pull request."""
        pr = pr_number or self._get_pr_number()
        if not pr:
            logger.warning("No PR number found — skipping comment")
            return

        url = f"{GITHUB_API}/repos/{self.repo}/issues/{pr}/comments"
        resp = httpx.post(url, headers=self._headers, json={"body": body}, timeout=15)

        if resp.status_code == 201:
            logger.info("Posted grading comment to PR #%d", pr)
        else:
            logger.error("Failed to post comment: %s %s", resp.status_code, resp.text[:200])

    def write_job_summary(self, markdown: str):
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if not summary_path:
            logger.warning("GITHUB_STEP_SUMMARY not set — not in Actions environment")
            return

        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(markdown + "\n")

    def set_output(self, name: str, value: str):
        """Write to GITHUB_OUTPUT for downstream steps."""
        output_path = os.environ.get("GITHUB_OUTPUT")
        if not output_path:
            return
        with open(output_path, "a", encoding="utf-8") as f:
            if "\n" in value:
                import uuid
                delimiter = f"ghadelimiter_{uuid.uuid4().hex[:8]}"
                f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{name}={value}\n")

    def _get_pr_number(self) -> int | None:
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if not event_path:
            return None

        try:
            event = json.loads(Path(event_path).read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return None

        # TODO: handle workflow_run events that re-trigger on forks
        pr = event.get("pull_request", {})
        return pr.get("number") or event.get("number")
