import json
import unittest
from unittest.mock import patch

import gitlab_api


class GitlabApiTests(unittest.TestCase):
    @patch("gitlab_api.subprocess.check_output")
    @patch("gitlab_api.get_authorized_user", return_value={"id": 7})
    def test_execute_issue_create_builds_expected_glab_command(self, _authorized_user, check_output):
        check_output.return_value = json.dumps({"iid": 12, "title": "Test"}).encode()

        result = gitlab_api.execute_issue_create(
            project_id=123,
            title="Test issue",
            labels=["Bug", "P::1"],
            milestone_id=456,
            epic={"id": 789},
            iteration={"id": 10},
            weight=3,
            estimated_time=60,
            issue_type="issue",
        )

        command = check_output.call_args.args[0]
        self.assertEqual(result, {"iid": 12, "title": "Test"})
        self.assertIn("/projects/123/issues", command)
        self.assertIn("title=Test issue", command)
        self.assertIn("assignee_ids=7", command)
        self.assertIn("labels=Bug,P::1", command)
        self.assertIn("milestone_id=456", command)
        self.assertIn("epic_id=789", command)
        self.assertIn("weight=3", command)
        self.assertIn("description=/iteration *iteration:10 \n/estimate 60m ", command)

    @patch("gitlab_api.subprocess.check_output")
    def test_create_branch_slug_matches_legacy_format(self, check_output):
        check_output.return_value = json.dumps({"name": "44-fix-login-flow"}).encode()

        gitlab_api.set_main_branch("main")
        result = gitlab_api.create_branch(5, {"iid": 44, "title": "Fix: Login (Flow)"})

        command = check_output.call_args.args[0]
        self.assertEqual(result, {"name": "44-fix-login-flow"})
        self.assertIn("branch=44-fix-login--flow", command)
        self.assertIn("ref=main", command)
        self.assertIn("issue_iid=44", command)

    @patch("gitlab_api.requests.get")
    @patch("gitlab_api.get_project_id", return_value=123)
    def test_get_merge_request_for_branch_filters_matching_branch(self, _project_id, get):
        get.return_value.status_code = 200
        get.return_value.json.return_value = [
            {"iid": 1, "source_branch": "other"},
            {"iid": 2, "source_branch": "feature"},
        ]

        self.assertEqual(
            gitlab_api.get_merge_request_for_branch("feature"),
            {"iid": 2, "source_branch": "feature"},
        )


if __name__ == "__main__":
    unittest.main()
