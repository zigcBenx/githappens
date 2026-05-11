import unittest
from unittest.mock import patch

from commands import create_issue, deploy, open_mr, report, review, summary
import main


class CommandTests(unittest.TestCase):
    def test_build_parser_accepts_review_select_flag(self):
        args = main.build_parser().parse_args(["review", "--select"])
        self.assertEqual(args.title, ["review"])
        self.assertTrue(args.select)

    def test_get_selected_iteration_matches_display_value(self):
        iterations = [{"start_date": "2026-01-01", "due_date": "2026-01-14", "id": 4}]
        self.assertEqual(
            create_issue.get_selected_iteration("2026-01-01 - 2026-01-14", iterations),
            iterations[0],
        )

    @patch("builtins.print")
    @patch("commands.review.api")
    @patch("commands.review.interactive.prompt_spent_time", return_value="15")
    @patch("commands.review.subprocess.run")
    def test_track_issue_time_posts_spend_note(self, run_mock, _prompt_mock, api_mock, _print_mock):
        api_mock.get_project_id.return_value = 10
        api_mock.get_current_issue_id.return_value = 20

        review.track_issue_time()

        command = run_mock.call_args.args[0]
        self.assertIn("/projects/10/issues/20/notes", command)
        self.assertIn("body=/spend 15m", command)

    @patch("builtins.print")
    def test_print_production_deploy_handles_finished_timestamp(self, print_mock):
        deploy._print_production_deploy(
            {
                "id": 1,
                "status": "success",
                "ref": "main",
                "sha": "abcdef123456",
                "web_url": "https://gitlab.example/pipelines/1",
            },
            {
                "name": "deploy",
                "status": "success",
                "started_at": "2026-01-01T00:00:00Z",
                "finished_at": "2026-01-01T00:05:00Z",
                "duration": 300,
            },
        )
        self.assertTrue(print_mock.called)

    @patch("commands.open_mr.webbrowser.open")
    @patch("commands.open_mr.subprocess.check_output", return_value="git@gitlab.example:group/project.git\n")
    @patch("commands.open_mr.api.get_active_merge_request_id", return_value=77)
    @patch("commands.open_mr.config.BASE_URL", "https://gitlab.example")
    def test_open_merge_request_uses_active_branch_mr(self, _mr_mock, _remote_mock, browser_mock):
        open_mr.open_merge_request_in_browser()
        browser_mock.assert_called_once_with("https://gitlab.example/group/project/-/merge_requests/77")

    @patch("commands.summary.git_utils.get_two_weeks_commits", return_value="commits")
    def test_summary_delegates_to_git_utils(self, commits_mock):
        self.assertEqual(summary.get_two_weeks_commits(), "commits")
        commits_mock.assert_called_once_with()

    @patch("commands.report.interactive.select_labels", return_value="Ops")
    @patch("commands.report.api.get_labels_of_group", return_value=[{"name": "Ops"}])
    def test_report_select_labels_uses_gitlab_labels(self, labels_mock, prompt_mock):
        self.assertEqual(report.select_labels("Department"), "Ops")
        labels_mock.assert_called_once_with("Department")
        prompt_mock.assert_called_once_with(["Ops"], multiple=False)


if __name__ == "__main__":
    unittest.main()
