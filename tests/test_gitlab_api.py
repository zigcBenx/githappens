import json
import unittest
from unittest.mock import patch

import gitlab_api


class GitLabApiTests(unittest.TestCase):
    @patch("gitlab_api.subprocess.check_output")
    @patch("gitlab_api.get_authorized_user")
    def test_execute_issue_create_builds_glab_payload(self, user_mock, check_output_mock):
        user_mock.return_value = {"id": 42}
        check_output_mock.return_value = json.dumps({"iid": 7, "title": "Fix bug"}).encode()

        issue = gitlab_api.execute_issue_create(
            project_id=123,
            title="Fix bug",
            labels=["bug", "api"],
            milestone_id=9,
            epic={"id": 1},
            iteration={"id": 5},
            weight=2,
            estimated_time=30,
        )

        command = check_output_mock.call_args.args[0]
        self.assertEqual(issue["iid"], 7)
        self.assertIn("labels=bug,api", command)
        self.assertIn("milestone_id=9", command)
        self.assertIn("epic_id=1", command)
        self.assertIn("weight=2", command)
        self.assertIn("description=/iteration *iteration:5 \n/estimate 30m ", command)

    @patch("gitlab_api.git_utils.get_project_link_from_current_dir")
    @patch("gitlab_api.get_all_projects")
    def test_get_project_id_matches_remote_ssh_url(self, get_all_projects_mock, remote_mock):
        remote_mock.return_value = "git@gitlab.com:group/project.git"
        get_all_projects_mock.return_value = [
            {"ssh_url_to_repo": "git@gitlab.com:group/project.git", "id": 101}
        ]
        self.assertEqual(gitlab_api.get_project_id(), 101)


if __name__ == "__main__":
    unittest.main()
