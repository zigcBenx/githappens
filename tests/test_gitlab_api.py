import json
import unittest
from unittest.mock import Mock, patch

import gitlab_api


class GitLabApiTests(unittest.TestCase):
    def test_get_all_projects_returns_json_for_success(self):
        response = Mock(status_code=200)
        response.json.return_value = [{"id": 1}]

        with patch("gitlab_api.requests.get", return_value=response) as get:
            projects = gitlab_api.get_all_projects("git@gitlab.com:group/project.git")

        self.assertEqual(projects, [{"id": 1}])
        self.assertIn("search=project", get.call_args.args[0])

    def test_create_issue_builds_glab_command(self):
        issue_payload = {"iid": 7, "title": "Fix bug"}

        with patch("gitlab_api.get_authorized_user", return_value={"id": 99}), \
                patch("gitlab_api.subprocess.check_output", return_value=json.dumps(issue_payload).encode()) as check_output:
            created = gitlab_api.create_issue(
                project_id=123,
                title="Fix bug",
                labels=["Bug", "P::1"],
                milestone_id=5,
                epic={"id": 8},
                iteration={"id": 13},
                weight=3,
                estimated_time=45,
            )

        command = check_output.call_args.args[0]
        self.assertEqual(created, issue_payload)
        self.assertIn("/projects/123/issues", command)
        self.assertIn("labels=Bug,P::1", command)
        self.assertIn("milestone_id=5", command)
        self.assertIn("description=/iteration *iteration:13 \n/estimate 45m ", command)

    def test_create_merge_request_includes_branch_options(self):
        mr_payload = {"iid": 11, "title": "Fix bug", "source_branch": "7-fix-bug"}

        with patch("gitlab_api.get_authorized_user", return_value={"id": 99}), \
                patch("gitlab_api.subprocess.check_output", return_value=json.dumps(mr_payload).encode()) as check_output:
            created = gitlab_api.create_merge_request(
                project_id=123,
                branch={"name": "7-fix-bug"},
                issue={"iid": 7, "title": "Fix bug"},
                labels=["Bug"],
                milestone_id=5,
                main_branch="main",
            )

        command = check_output.call_args.args[0]
        self.assertEqual(created, mr_payload)
        self.assertIn("target_branch=main", command)
        self.assertIn("remove_source_branch=true", command)
        self.assertIn("squash=true", command)


if __name__ == "__main__":
    unittest.main()
