import io
import os
import sys
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from githappens.commands.deploy import get_last_production_deploy
from githappens.commands.create_issue import process_report, start_issue_creation
from githappens.commands.open_mr import open_merge_request_in_browser
from githappens.commands.review import get_merge_request_for_current_branch, track_issue_time
from githappens.commands.summary import generate_smart_summary
from githappens.gitlab_api import GitLabApiError


class SummaryCommandTests(unittest.TestCase):
    def test_generate_smart_summary_keeps_legacy_openai_error_message(self):
        runtime = types.SimpleNamespace(config=types.SimpleNamespace(openai_api_key="sk-test"))
        fake_openai = types.SimpleNamespace()
        fake_openai.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=mock.Mock(side_effect=RuntimeError("quota exceeded"))
            )
        )

        output = io.StringIO()
        with mock.patch.dict(sys.modules, {"openai": fake_openai}), redirect_stdout(output):
            generate_smart_summary(runtime, "2026-01-01 - dev@example.com - commit")

        self.assertIn("Error generating AI summary: quota exceeded", output.getvalue())


class ReviewCommandTests(unittest.TestCase):
    def test_missing_merge_request_raises_domain_error(self):
        client = mock.Mock()
        client.get_merge_request_for_branch.return_value = None

        with mock.patch("githappens.commands.review.get_current_branch", return_value="feature/test"):
            with self.assertRaisesRegex(GitLabApiError, "No open merge request found"):
                get_merge_request_for_current_branch(client, 123)

    def test_time_tracking_failure_is_non_fatal(self):
        client = mock.Mock()
        client.add_issue_note.side_effect = RuntimeError("note failed")

        output = io.StringIO()
        with mock.patch("githappens.commands.review.get_current_issue_id", return_value="99"):
            with mock.patch("githappens.commands.review.prompt_spent_time", return_value="15"):
                with redirect_stdout(output):
                    track_issue_time(client, 123)

        client.add_issue_note.assert_called_once_with(123, "99", "/spend 15m")
        self.assertIn("Error tracking issue time: note failed", output.getvalue())


class DeployCommandTests(unittest.TestCase):
    def test_last_deploy_defaults_to_legacy_master_ref(self):
        runtime = types.SimpleNamespace(
            config=types.SimpleNamespace(production_ref=None),
            main_branch="main",
            production_mappings={},
        )
        client = mock.Mock()
        client.get_pipelines.return_value = []

        with redirect_stdout(io.StringIO()):
            get_last_production_deploy(runtime, client, 123)

        self.assertEqual(client.get_pipelines.call_args.kwargs["ref"], "master")


class OpenMergeRequestCommandTests(unittest.TestCase):
    def test_open_merge_request_builds_browser_url(self):
        runtime = types.SimpleNamespace(
            config=types.SimpleNamespace(base_url="https://gitlab.example.com")
        )
        client = mock.Mock()

        with mock.patch(
            "githappens.commands.open_mr.get_merge_request_for_current_branch",
            return_value={"iid": 42},
        ):
            with mock.patch(
                "githappens.commands.open_mr.get_project_link_from_current_dir",
                return_value="git@gitlab.example.com:team/repo.git",
            ):
                with mock.patch("webbrowser.open") as open_browser:
                    open_merge_request_in_browser(runtime, client, 123)

        open_browser.assert_called_once_with(
            "https://gitlab.example.com/team/repo/-/merge_requests/42"
        )


class EntrypointTests(unittest.TestCase):
    def test_legacy_entrypoint_is_executable(self):
        entrypoint = Path(__file__).resolve().parent.parent / "gitHappens.py"
        self.assertTrue(os.access(entrypoint, os.X_OK))


class IssueCreationCommandTests(unittest.TestCase):
    def test_start_issue_creation_adds_estimated_time_for_only_issue(self):
        runtime = types.SimpleNamespace()
        client = mock.Mock()
        client.create_issue.return_value = {"iid": 7, "title": "Test issue"}

        with mock.patch("githappens.commands.create_issue.prompt_estimated_time", return_value="30"):
            with redirect_stdout(io.StringIO()):
                created = start_issue_creation(
                    runtime,
                    client,
                    project_id=123,
                    title="Test issue",
                    milestone_id=False,
                    epic=False,
                    iteration=False,
                    selected_settings={"labels": ["bug"]},
                    only_issue=True,
                )

        self.assertEqual(created["iid"], 7)
        self.assertEqual(client.create_issue.call_args.args[7], 30)

    def test_process_report_attempts_time_tracking_when_close_fails(self):
        runtime = types.SimpleNamespace(
            config=types.SimpleNamespace(incident_project_id="456")
        )
        client = mock.Mock()
        client.list_group_labels.return_value = []
        client.create_issue.return_value = {"iid": 11, "title": "Incident Report: outage"}
        client.close_issue.side_effect = RuntimeError("close failed")

        output = io.StringIO()
        with mock.patch("githappens.commands.create_issue.select_labels", return_value=None):
            with mock.patch("githappens.commands.create_issue.get_active_iteration", return_value={"id": 2}):
                with redirect_stdout(output):
                    process_report(runtime, client, "outage", 15)

        client.close_issue.assert_called_once_with("456", 11)
        client.add_issue_spent_time.assert_called_once_with("456", 11, 15)
        self.assertIn("Incident issue #11 created successfully.", output.getvalue())
        self.assertIn("Error closing issue: close failed", output.getvalue())
