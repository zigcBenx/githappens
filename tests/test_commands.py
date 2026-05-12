import unittest
from unittest.mock import patch

from commands import create_issue, deploy, open_mr, review


class CommandTests(unittest.TestCase):
    def test_start_issue_creation_splits_estimated_time_for_multiple_projects(self):
        settings = {"labels": ["Bug"]}
        created_issue = {"iid": 1, "title": "Fix bug"}

        with patch("commands.create_issue.interactive.prompt_estimated_time", return_value="60"), \
                patch("commands.create_issue.create_issue", return_value=created_issue) as create_issue_call, \
                patch("builtins.print"):
            result = create_issue.start_issue_creation(
                project_id=[123, 456],
                title="Fix bug",
                milestone=False,
                epic=False,
                iteration=False,
                selected_settings=settings,
                only_issue=True,
                main_branch="main",
            )

        self.assertEqual(result, created_issue)
        self.assertEqual(create_issue_call.call_args.args[5]["estimated_time"], 30)

    def test_get_current_issue_id_reads_closes_description(self):
        with patch("commands.review.git_utils.get_current_branch", return_value="1-fix"), \
                patch("commands.review.get_merge_request_for_branch", return_value={"description": '"Closes #42"'}):
            self.assertEqual(review.get_current_issue_id(), "42")

    def test_deploy_finds_project_mapping_job(self):
        pipeline = {
            "id": 1,
            "status": "success",
            "ref": "master",
            "sha": "abcdef123",
            "web_url": "https://gitlab.example/pipelines/1",
        }
        job = {
            "name": "production:deploy",
            "stage": "deploy",
            "status": "success",
            "started_at": "2026-05-12T09:00:00Z",
            "finished_at": "2026-05-12T09:05:00Z",
            "duration": 300,
        }

        with patch("commands.deploy.git_utils.resolve_project_id", return_value="9418557"), \
                patch.dict("commands.deploy.PRODUCTION_MAPPINGS", {"9418557": {"stage": "deploy", "job": "production:deploy"}}, clear=True), \
                patch("commands.deploy.gitlab_api.list_pipelines", return_value=[pipeline]), \
                patch("commands.deploy.gitlab_api.list_pipeline_jobs", return_value=[job]), \
                patch("builtins.print") as print_call:
            deploy.get_last_production_deploy()

        printed = "\n".join(str(call.args[0]) for call in print_call.call_args_list if call.args)
        self.assertIn("Last Production Deployment:", printed)
        self.assertIn("production:deploy", printed)

    def test_open_merge_request_in_browser_builds_gitlab_url(self):
        with patch("commands.open_mr.get_active_merge_request_id", return_value=12), \
                patch("commands.open_mr.subprocess.check_output", return_value="git@gitlab.com:group/project.git\n"), \
                patch("commands.open_mr.webbrowser.open") as open_browser:
            open_mr.open_merge_request_in_browser()

        self.assertTrue(open_browser.call_args.args[0].endswith("/group/project/-/merge_requests/12"))


if __name__ == "__main__":
    unittest.main()
