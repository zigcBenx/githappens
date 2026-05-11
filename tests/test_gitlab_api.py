import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from config import AppSettings
from gitlab_api import GitLabAPI


def make_settings(**overrides):
    values = {
        "base_url": "https://gitlab.example.com",
        "group_id": "42",
        "custom_template": "Custom",
        "gitlab_token": "token",
        "delete_branch": True,
        "developer_email": None,
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


class GitLabAPITests(unittest.TestCase):
    def test_get_all_projects_searches_by_remote_name(self):
        response = SimpleNamespace(status_code=200, json=lambda: [{"id": 1}])
        http = SimpleNamespace(get=Mock(return_value=response))
        api = GitLabAPI(make_settings(), http_client=http)

        self.assertEqual(api.get_all_projects("git@gitlab.com:team/app.git"), [{"id": 1}])
        http.get.assert_called_once_with(
            "https://gitlab.example.com/api/v4/projects",
            headers={"Private-Token": "token"},
            params={"membership": "true", "search": "app"},
        )

    def test_create_issue_builds_glab_command(self):
        api = GitLabAPI(make_settings())
        api.get_authorized_user = Mock(return_value={"id": 7})

        with patch("gitlab_api.subprocess.check_output", return_value=b'{"iid": 3, "title": "Fix"}') as check_output:
            issue = api.create_issue(
                project_id=10,
                title="Fix bug",
                labels=["Bug", "P::1"],
                milestone_id=20,
                epic={"id": 30},
                iteration={"id": 40},
                weight=2,
                estimated_time=90,
            )

        command = check_output.call_args[0][0]
        self.assertEqual(issue["iid"], 3)
        self.assertIn("/projects/10/issues", command)
        self.assertIn("labels=Bug,P::1", command)
        self.assertIn("milestone_id=20", command)
        self.assertIn("epic_id=30", command)
        self.assertIn("weight=2", command)
        self.assertIn("description=/iteration *iteration:40 \n/estimate 90m ", command)

    def test_create_merge_request_respects_settings(self):
        api = GitLabAPI(make_settings(delete_branch=True, squash_commits=True))
        api.get_authorized_user = Mock(return_value={"id": 7})

        with patch("gitlab_api.subprocess.check_output", return_value=b'{"iid": 5, "title": "Fix", "source_branch": "3-fix"}') as check_output:
            api.create_merge_request(
                project_id=10,
                branch={"name": "3-fix"},
                issue={"iid": 3, "title": "Fix"},
                labels=["Bug"],
                milestone_id=20,
                main_branch="master",
            )

        command = check_output.call_args[0][0]
        self.assertIn("/projects/10/merge_requests", command)
        self.assertIn("source_branch=3-fix", command)
        self.assertIn("target_branch=master", command)
        self.assertIn("squash=true", command)
        self.assertIn("remove_source_branch=true", command)


if __name__ == "__main__":
    unittest.main()
