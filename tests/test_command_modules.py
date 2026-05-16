from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from githappens.commands.open_mr import open_merge_request_in_browser
from githappens.commands.report import process_report
from githappens.config import AppConfig
from githappens.gitlab_api import create_issue, create_merge_request, execute_issue_create


def make_config(base_dir: Path) -> AppConfig:
    return AppConfig(
        base_dir=base_dir,
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
        reviewers=[11, 22],
        production_mappings={},
    )


class ReportCommandTests(unittest.TestCase):
    def test_process_report_creates_incident_issue_and_tracks_time(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            config_dir = root / "configs"
            config_dir.mkdir()
            (config_dir / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "incident_project_id=456",
                    ]
                ),
                encoding="utf-8",
            )
            config = make_config(root)

            with patch("githappens.commands.report.get_labels_of_group", return_value=[{"name": "Ops"}]), patch(
                "githappens.commands.report.select_labels", return_value="Department::Ops"
            ), patch("githappens.commands.report.get_active_iteration", return_value={"id": 7}), patch(
                "githappens.commands.report.create_issue", return_value={"iid": 99}
            ) as create_issue_mock, patch("githappens.commands.report.close_opened_issue") as close_issue, patch(
                "githappens.commands.report.add_spent_time"
            ) as add_time:
                process_report(config, "Database outage", 25)

        create_issue_mock.assert_called_once_with(
            config,
            "Incident Report: Database outage",
            "456",
            False,
            False,
            {"id": 7},
            {
                "labels": ["incident", "report", "Department::Ops"],
                "onlyIssue": True,
                "type": "incident",
            },
        )
        close_issue.assert_called_once_with(config, 99, "456")
        add_time.assert_called_once_with("456", 99, 25)


class OpenMergeRequestTests(unittest.TestCase):
    def test_open_merge_request_uses_current_branch_and_remote_path(self) -> None:
        config = make_config(Path("."))

        with patch("githappens.commands.open_mr.get_current_branch", return_value="feature/refactor"), patch(
            "githappens.commands.open_mr.find_merge_request_id_by_branch", return_value=42
        ) as find_mr, patch(
            "githappens.commands.open_mr.subprocess.check_output",
            return_value="git@gitlab.example.com:team/project.git\n",
        ), patch("githappens.commands.open_mr.webbrowser.open") as open_browser:
            open_merge_request_in_browser(config)

        find_mr.assert_called_once_with(config, "feature/refactor")
        open_browser.assert_called_once_with("https://gitlab.example.com/team/project/-/merge_requests/42")

    def test_open_merge_request_ignores_git_lookup_failures(self) -> None:
        config = make_config(Path("."))

        with patch("githappens.commands.open_mr.get_current_branch", side_effect=subprocess.CalledProcessError(1, "git")), patch(
            "githappens.commands.open_mr.webbrowser.open"
        ) as open_browser:
            open_merge_request_in_browser(config)

        open_browser.assert_not_called()


class GitLabApiCommandTests(unittest.TestCase):
    def test_execute_issue_create_includes_custom_issue_type(self) -> None:
        config = make_config(Path("."))
        captured_command: list[str] = []

        def fake_check_output(command: list[str]) -> bytes:
            captured_command.extend(command)
            return json.dumps({"iid": 12}).encode("utf-8")

        with patch("githappens.gitlab_api.get_authorized_user", return_value={"id": 3}), patch(
            "githappens.gitlab_api.subprocess.check_output", side_effect=fake_check_output
        ):
            issue = execute_issue_create(
                config,
                "456",
                "Incident Report: Database outage",
                ["incident", "report"],
                False,
                False,
                {"id": 7},
                None,
                25,
                issue_type="incident",
            )

        self.assertEqual(issue["iid"], 12)
        self.assertIn("issue_type=incident", captured_command)
        self.assertIn("labels=incident,report", captured_command)
        self.assertIn("description=/iteration *iteration:7 \n/estimate 25m ", captured_command)

    def test_create_issue_defaults_to_standard_issue_type(self) -> None:
        config = make_config(Path("."))

        with patch("githappens.gitlab_api.execute_issue_create", return_value={"iid": 8}) as execute:
            issue = create_issue(config, "Refactor CLI", "456", False, False, False, {"labels": ["tech-debt"]})

        self.assertEqual(issue["iid"], 8)
        execute.assert_called_once_with(config, "456", "Refactor CLI", ["tech-debt"], False, False, False, None, None, "issue")

    def test_create_merge_request_respects_configured_cleanup_and_labels(self) -> None:
        config = make_config(Path("."))
        captured_command: list[str] = []

        def fake_check_output(command: list[str]) -> bytes:
            captured_command.extend(command)
            return json.dumps({"iid": 44}).encode("utf-8")

        with patch("githappens.gitlab_api.get_authorized_user", return_value={"id": 3}), patch(
            "githappens.gitlab_api.subprocess.check_output", side_effect=fake_check_output
        ):
            merge_request = create_merge_request(
                config,
                "456",
                {"name": "116-refactor-cli"},
                {"iid": 116, "title": "Refactor CLI"},
                ["tech-debt", "refactor"],
                9,
            )

        self.assertEqual(merge_request["iid"], 44)
        self.assertIn("source_branch=116-refactor-cli", captured_command)
        self.assertIn("target_branch=master", captured_command)
        self.assertIn("squash=true", captured_command)
        self.assertIn("remove_source_branch=true", captured_command)
        self.assertIn("labels=tech-debt,refactor", captured_command)
        self.assertIn("milestone_id=9", captured_command)


if __name__ == "__main__":
    unittest.main()
