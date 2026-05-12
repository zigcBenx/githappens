import unittest
from types import SimpleNamespace
from unittest.mock import patch

from githappens.commands import deploy, issues, open_mr, report, review, summary


class FakePrompt:
    class Text:
        def __init__(self, *args, **kwargs):
            pass

    @staticmethod
    def prompt(_):
        return {"estimated_time": "30", "spent_time": "45"}


class IssuesCommandTest(unittest.TestCase):
    @patch("githappens.commands.issues.gitlab_api.create_merge_request")
    @patch("githappens.commands.issues.gitlab_api.create_branch")
    @patch("githappens.commands.issues.gitlab_api.execute_issue_create")
    @patch("githappens.commands.issues.interactive._inquirer", return_value=FakePrompt)
    def test_start_issue_creation_creates_issue_branch_and_mr(
        self, _, execute_issue_create, create_branch, create_merge_request
    ):
        ctx = SimpleNamespace(main_branch="main")
        execute_issue_create.return_value = {"iid": 10, "title": "Fix bug"}
        create_branch.return_value = {"name": "10-fix-bug"}
        create_merge_request.return_value = {
            "iid": 20,
            "title": "Fix bug",
            "source_branch": "10-fix-bug",
        }

        with patch("builtins.print"):
            created_issue = issues.start_issue_creation(
                ctx,
                project_id=123,
                title="Fix bug",
                milestone_id=5,
                epic=None,
                iteration=None,
                selected_settings={"labels": ["bug"]},
                only_issue=False,
            )

        self.assertEqual(created_issue["iid"], 10)
        execute_issue_create.assert_called_once()
        self.assertEqual(execute_issue_create.call_args.args[8], 30)
        create_branch.assert_called_once_with(ctx, 123, created_issue)
        create_merge_request.assert_called_once()

    @patch("githappens.commands.issues.gitlab_api.create_branch")
    @patch("githappens.commands.issues.gitlab_api.execute_issue_create")
    @patch("githappens.commands.issues.interactive._inquirer", return_value=FakePrompt)
    def test_start_issue_creation_can_stop_after_issue(
        self, _, execute_issue_create, create_branch
    ):
        execute_issue_create.return_value = {"iid": 11, "title": "Docs"}

        with patch("builtins.print"):
            result = issues.start_issue_creation(
                SimpleNamespace(),
                123,
                "Docs",
                False,
                None,
                None,
                {"labels": ["docs"]},
                True,
            )

        self.assertEqual(result["iid"], 11)
        create_branch.assert_not_called()


class OpenMrCommandTest(unittest.TestCase):
    @patch("githappens.commands.open_mr.webbrowser.open")
    @patch("githappens.commands.open_mr.subprocess.check_output")
    @patch("githappens.commands.open_mr.get_active_merge_request_id", return_value=7)
    def test_open_merge_request_builds_url_from_remote(self, _, check_output, browser_open):
        check_output.return_value = "git@gitlab.example.test:group/project.git\n"
        ctx = SimpleNamespace(settings=SimpleNamespace(base_url="https://gitlab.example.test"))

        open_mr.open_merge_request_in_browser(ctx)

        browser_open.assert_called_once_with(
            "https://gitlab.example.test/group/project/-/merge_requests/7"
        )


class ReviewCommandTest(unittest.TestCase):
    @patch("githappens.commands.review.subprocess.run")
    @patch("githappens.commands.review.interactive._inquirer", return_value=FakePrompt)
    @patch("githappens.commands.review.get_current_issue_id", return_value="10")
    @patch("githappens.commands.review.gitlab_api.get_project_id", return_value=123)
    def test_track_issue_time_posts_spent_time_note(self, _, __, ___, run):
        with patch("builtins.print"):
            review.track_issue_time(SimpleNamespace())

        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertIn("/projects/123/issues/10/notes", command)
        self.assertIn("body=/spend 45m", command)

    @patch("ai_code_review.run_review_for_mr")
    @patch("githappens.commands.review.gitlab_api.get_project_id", return_value=123)
    @patch("githappens.commands.review.gitlab_api.set_merge_request_to_auto_merge")
    @patch("githappens.commands.review.gitlab_api.add_reviewers_to_merge_request")
    @patch("githappens.commands.review.get_active_merge_request_id", return_value=20)
    @patch("githappens.commands.review.track_issue_time")
    def test_review_current_merge_request_adds_reviewers_and_auto_merge(
        self, track_issue_time, _, add_reviewers, auto_merge, get_project_id, run_review
    ):
        ctx = SimpleNamespace(
            reviewers=[1, 2],
            settings=SimpleNamespace(gitlab_token="token", api_url="https://gitlab/api/v4"),
        )

        with patch("builtins.print"):
            review.review_current_merge_request(ctx, auto_merge=True)

        track_issue_time.assert_called_once_with(ctx)
        add_reviewers.assert_called_once_with(ctx, 20, reviewers=None)
        get_project_id.assert_called_once_with(ctx)
        run_review.assert_called_once()
        auto_merge.assert_called_once_with(ctx, 20)


class ReportCommandTest(unittest.TestCase):
    @patch("githappens.commands.report.subprocess.run")
    @patch("githappens.commands.report.gitlab_api.close_opened_issue")
    @patch("githappens.commands.report.create_issue")
    @patch("githappens.commands.report.interactive.get_active_iteration")
    @patch("githappens.commands.report.interactive.select_labels", return_value="Support")
    def test_process_report_creates_closes_and_tracks_incident(
        self, _, get_active_iteration, create_issue, close_opened_issue, run
    ):
        ctx = SimpleNamespace(settings=SimpleNamespace(incident_project_id="incidents"))
        get_active_iteration.return_value = {"id": 3}
        create_issue.return_value = {"iid": 99}

        with patch("builtins.print"):
            report.process_report(ctx, "Checkout outage", 15)

        settings = create_issue.call_args.args[6]
        self.assertEqual(settings["labels"], ["incident", "report", "Support"])
        self.assertEqual(settings["type"], "incident")
        close_opened_issue.assert_called_once_with("incidents", 99)
        self.assertIn("duration=15m", run.call_args.args[0])

    @patch("githappens.commands.report.create_issue")
    def test_process_report_returns_when_incident_project_missing(self, create_issue):
        ctx = SimpleNamespace(settings=SimpleNamespace(incident_project_id=None))

        with patch("builtins.print"):
            report.process_report(ctx, "Checkout outage", 15)

        create_issue.assert_not_called()


class SummaryCommandTest(unittest.TestCase):
    @patch("githappens.commands.summary.git_utils.get_two_weeks_commits")
    def test_print_commit_summary_delegates_to_git_helper(self, get_commits):
        ctx = SimpleNamespace()

        summary.print_commit_summary(ctx)

        get_commits.assert_called_once_with(ctx)


class DeployCommandTest(unittest.TestCase):
    @patch("githappens.commands.deploy.gitlab_api.get_pipeline_jobs")
    @patch("githappens.commands.deploy.gitlab_api.get_pipelines")
    @patch("githappens.commands.deploy.gitlab_api.get_project_id", return_value=123)
    def test_get_last_production_deploy_uses_project_mapping(
        self, _, get_pipelines, get_pipeline_jobs
    ):
        ctx = SimpleNamespace(
            main_branch="main",
            production_mappings={"123": {"stage": "deploy", "job": "production"}},
        )
        get_pipelines.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: [
                {
                    "id": 8,
                    "status": "success",
                    "ref": "main",
                    "sha": "abcdef123456",
                    "web_url": "https://gitlab/pipeline/8",
                }
            ],
        )
        get_pipeline_jobs.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: [
                {
                    "name": "production",
                    "stage": "deploy",
                    "status": "success",
                    "started_at": "2026-05-01T00:00:00Z",
                    "finished_at": "2026-05-01T00:01:00Z",
                    "duration": 60,
                }
            ],
        )

        with patch("builtins.print"):
            deploy.get_last_production_deploy(ctx)

        get_pipelines.assert_called_once()
        self.assertEqual(get_pipelines.call_args.args[2]["ref"], "main")
        get_pipeline_jobs.assert_called_once_with(ctx, 123, 8)


if __name__ == "__main__":
    unittest.main()
