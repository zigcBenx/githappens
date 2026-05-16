from __future__ import annotations

import contextlib
import io
import unittest
from pathlib import Path
from unittest.mock import patch

from githappens.commands.deploy import _job_matches
from githappens.config import AppConfig
from githappens.main import run


def make_config() -> AppConfig:
    return AppConfig(
        base_dir=Path("."),
        base_url="https://gitlab.example.com",
        api_url="https://gitlab.example.com/api/v4",
        group_id="123",
        custom_template="Custom",
        gitlab_token="token",
        delete_branch=True,
        developer_email=None,
        squash_commits=True,
        production_pipeline_name="deploy",
        production_job_name=None,
        production_ref=None,
        templates=[],
        reviewers=[],
        production_mappings={"123": {"stage": "production", "job": "deploy-prod"}},
    )


class MainDispatchTests(unittest.TestCase):
    def test_run_dispatches_open_command(self) -> None:
        config = make_config()
        with patch("githappens.main.load_app_config", return_value=config), patch(
            "githappens.main.open_merge_request_in_browser"
        ) as open_mr:
            run(["open"])

        open_mr.assert_called_once_with(config)

    def test_run_dispatches_report_command(self) -> None:
        config = make_config()
        with patch("githappens.main.load_app_config", return_value=config), patch(
            "githappens.main.process_report"
        ) as process_report:
            run(["report", "Production incident", "25"])

        process_report.assert_called_once_with(config, "Production incident", 25)

    def test_run_rejects_invalid_report_minutes(self) -> None:
        config = make_config()
        output = io.StringIO()
        with patch("githappens.main.load_app_config", return_value=config), patch(
            "githappens.main.process_report", side_effect=AssertionError("should not dispatch")
        ), contextlib.redirect_stdout(output):
            run(["report", "Production incident", "later"])

        self.assertIn("Invalid minutes", output.getvalue())


class DeploymentMatchingTests(unittest.TestCase):
    def test_job_matches_configured_stage_or_job_name(self) -> None:
        config = make_config()

        self.assertTrue(_job_matches(config, "123", "production", "anything"))
        self.assertTrue(_job_matches(config, "123", "deploy", "deploy-prod"))
        self.assertFalse(_job_matches(config, "123", "test", "unit-tests"))

    def test_job_match_fails_when_project_mapping_is_absent(self) -> None:
        config = make_config()
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            result = _job_matches(config, "999", "production", "deploy-prod")

        self.assertFalse(result)
        self.assertIn("Didn't find deployment pipeline", output.getvalue())


if __name__ == "__main__":
    unittest.main()
