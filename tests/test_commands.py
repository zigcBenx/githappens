import io
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

from commands.create_issue import resolve_project_id, start_issue_creation
from commands.deploy import _matches_default_production_job, _matches_production_mapping
from commands.open_mr import open_merge_request_in_browser
from commands.review import submit_for_review
from commands.summary import generate_smart_summary
from config import AppSettings


def make_settings(**overrides):
    values = {
        "base_url": "https://gitlab.example.com",
        "group_id": "42",
        "custom_template": "Custom",
        "gitlab_token": "token",
        "delete_branch": True,
        "developer_email": "dev@example.com",
        "squash_commits": True,
        "production_pipeline_name": "deploy",
        "production_job_name": None,
        "production_ref": None,
        "openai_api_key": None,
        "incident_project_id": None,
        "templates": [],
        "reviewers": [1, 2],
        "production_mappings": {},
    }
    values.update(overrides)
    return AppSettings(**values)


class FakeCreateIssueAPI:
    def __init__(self):
        self.issue_args = None

    def create_issue(self, *args):
        self.issue_args = args
        return {"iid": 4, "title": "Fix bug"}

    def create_branch(self, project_id, issue, main_branch):
        return {"name": "4-fix-bug"}

    def create_merge_request(self, *args):
        return {"iid": 9, "title": "Fix bug", "source_branch": "4-fix-bug"}


class CommandTests(unittest.TestCase):
    def test_resolve_project_id_matches_remote_ssh_url(self):
        api = SimpleNamespace(
            get_all_projects=Mock(
                return_value=[
                    {"id": 1, "ssh_url_to_repo": "git@gitlab.com:team/other.git"},
                    {"id": 2, "ssh_url_to_repo": "git@gitlab.com:team/app.git"},
                ]
            )
        )

        with patch("commands.create_issue.git_utils.get_project_link_from_current_dir", return_value="git@gitlab.com:team/app.git"):
            self.assertEqual(resolve_project_id(api), 2)

    def test_start_issue_creation_adds_estimated_time_and_creates_mr(self):
        api = FakeCreateIssueAPI()
        selected_settings = {"labels": ["Bug"], "weight": 2}

        with patch("commands.create_issue.interactive.prompt_estimated_time", return_value="60"), \
            redirect_stdout(io.StringIO()):
            issue = start_issue_creation(
                api,
                "Fix bug",
                10,
                20,
                {"id": 30},
                {"id": 40},
                selected_settings,
                False,
                "master",
            )

        self.assertEqual(issue["iid"], 4)
        self.assertEqual(api.issue_args[7], 60)

    def test_open_merge_request_in_browser_uses_existing_remote_shape(self):
        api = SimpleNamespace(get_merge_request_for_branch=Mock(return_value={"iid": 11}))
        settings = make_settings()

        with patch("commands.open_mr.resolve_project_id", return_value=10), \
            patch("commands.open_mr.git_utils.get_current_branch", return_value="feature"), \
            patch("commands.open_mr.git_utils.get_remote_origin_url", return_value="git@gitlab.example.com:team/app.git"), \
            patch("commands.open_mr.webbrowser.open") as browser_open:
            open_merge_request_in_browser(api, settings)

        browser_open.assert_called_once_with("https://gitlab.example.com/team/app/-/merge_requests/11")

    def test_submit_for_review_tracks_time_and_assigns_default_reviewers(self):
        api = SimpleNamespace(
            add_time_tracking_note=Mock(),
            add_reviewers_to_merge_request=Mock(),
            set_merge_request_to_auto_merge=Mock(),
        )
        settings = make_settings()

        with patch("commands.review.get_active_merge_request", return_value=({"iid": 5, "description": '"Closes #123"'}, 10)), \
            patch("commands.review.interactive.prompt_spent_time", return_value="15"), \
            patch("ai_code_review.run_review_for_mr"), \
            redirect_stdout(io.StringIO()):
            submit_for_review(api, settings)

        api.add_time_tracking_note.assert_called_once_with(10, "123", "15")
        api.add_reviewers_to_merge_request.assert_called_once_with(10, 5, reviewers=None)

    def test_deploy_matching_helpers(self):
        self.assertTrue(_matches_production_mapping({"stage": "deploy", "name": "job"}, {"stage": "deploy"}))
        self.assertTrue(_matches_default_production_job({"stage": "deploy", "name": "job"}, make_settings()))

    def test_generate_smart_summary_skips_without_openai_key(self):
        with patch("commands.summary.git_utils.get_two_weeks_commits", return_value="2026-01-01 - dev@example.com - Fix"), \
            patch("builtins.print") as print_mock:
            generate_smart_summary(make_settings(openai_api_key=None))

        print_mock.assert_called_with("OpenAI API key not set. Skipping AI summary generation.")


if __name__ == "__main__":
    unittest.main()
