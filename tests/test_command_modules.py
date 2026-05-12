import datetime
import io
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import gitlab_api
from commands.deploy import get_last_production_deploy
from commands.open_mr import open_merge_request_in_browser
from commands.report import process_report
from commands.review import get_current_issue_id
from commands.summary import generate_smart_summary


class CommandModuleTests(unittest.TestCase):
    @patch("commands.open_mr.webbrowser.open")
    @patch("commands.open_mr.subprocess.check_output", return_value="git@gitlab.com:group/repo.git\n")
    @patch("commands.open_mr.get_active_merge_request_id", return_value=12)
    def test_open_merge_request_in_browser_builds_gitlab_url(self, _mr_id, _remote, browser_open):
        open_merge_request_in_browser()

        browser_open.assert_called_once_with("https://gitlab.com/group/repo/-/merge_requests/12")

    @patch("commands.review.get_current_branch", return_value="feature")
    @patch(
        "commands.review.get_merge_request_for_branch",
        return_value={"description": '"Closes #99"'},
    )
    def test_get_current_issue_id_extracts_issue_from_mr_description(self, _mr, _branch):
        self.assertEqual(get_current_issue_id(), "99")

    @patch("commands.summary.get_two_weeks_commits", return_value="")
    def test_generate_smart_summary_stops_when_no_commits(self, commits):
        generate_smart_summary()

        commits.assert_called_once_with(return_output=True)

    @patch("commands.report.subprocess.run")
    @patch("commands.report.close_opened_issue")
    @patch("commands.report.create_issue")
    @patch("commands.report.get_active_iteration", return_value={"id": 5})
    @patch("commands.report.select_labels", return_value="Department")
    def test_process_report_creates_and_closes_incident_issue(
        self,
        _labels,
        _iteration,
        create_issue,
        close_opened_issue,
        _run,
    ):
        create_issue.return_value = {"iid": 77}

        with patch("commands.report.CONFIG", SimpleNamespace(incident_project_id="123")):
            process_report("Something happened", 15)

        create_issue.assert_called_once_with(
            "Incident Report: Something happened",
            "123",
            False,
            False,
            {"id": 5},
            {
                "labels": ["incident", "report", "Department"],
                "onlyIssue": True,
                "type": "incident",
            },
        )
        close_opened_issue.assert_called_once_with(77, "123")

    @patch("commands.deploy.requests.get")
    @patch("commands.deploy.get_project_id", return_value=123)
    def test_get_last_production_deploy_prints_matching_successful_job(self, _project_id, get):
        gitlab_api.set_main_branch("main")
        pipeline_response = Mock(status_code=200)
        pipeline_response.json.return_value = [
            {
                "id": 10,
                "status": "success",
                "ref": "main",
                "sha": "abcdef123456",
                "web_url": "https://gitlab.example/pipeline/10",
            }
        ]
        jobs_response = Mock(status_code=200)
        jobs_response.json.return_value = [
            {
                "name": "production:deploy",
                "stage": "deploy",
                "status": "success",
                "started_at": "2026-01-01T00:00:00Z",
                "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "duration": 42,
            }
        ]
        get.side_effect = [pipeline_response, jobs_response]

        with patch("commands.deploy.PRODUCTION_MAPPINGS", {"123": {"stage": "deploy", "job": "production:deploy"}}):
            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                get_last_production_deploy()

        self.assertIn("Last Production Deployment", stdout.getvalue())
        self.assertIn("Pipeline: #10 - success", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
