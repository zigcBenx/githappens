import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from githappens import gitlab_api


class GitlabApiTest(unittest.TestCase):
    @patch("githappens.gitlab_api.get_authorized_user", return_value={"id": 7})
    @patch("githappens.gitlab_api.subprocess.check_output")
    def test_execute_issue_create_builds_command_payload(self, check_output, _):
        check_output.return_value = json.dumps({"iid": 10}).encode()

        issue = gitlab_api.execute_issue_create(
            SimpleNamespace(),
            project_id=123,
            title="Fix bug",
            labels=["bug", "ui"],
            milestone_id=5,
            epic={"id": 9},
            iteration={"id": 11},
            weight=3,
            estimated_time=30,
        )

        command = check_output.call_args.args[0]
        self.assertEqual(issue, {"iid": 10})
        self.assertIn("/projects/123/issues", command)
        self.assertIn("title=Fix bug", command)
        self.assertIn("assignee_ids=7", command)
        self.assertIn("labels=bug,ui", command)
        self.assertIn("milestone_id=5", command)
        self.assertIn("epic_id=9", command)
        self.assertIn("weight=3", command)
        self.assertIn("description=/iteration *iteration:11 \n/estimate 30m ", command)

    @patch("githappens.gitlab_api.get_authorized_user", return_value={"id": 7})
    @patch("githappens.gitlab_api.subprocess.check_output")
    def test_create_merge_request_honors_configured_flags(self, check_output, _):
        check_output.return_value = json.dumps({"iid": 20}).encode()
        ctx = SimpleNamespace(
            main_branch="main",
            settings=SimpleNamespace(
                squash_commits=True,
                delete_branch_after_merge=True,
            ),
        )

        mr = gitlab_api.create_merge_request(
            ctx,
            project_id=123,
            branch={"name": "10-fix-bug"},
            issue={"iid": 10, "title": "Fix bug"},
            labels=["bug"],
            milestone_id=5,
        )

        command = check_output.call_args.args[0]
        self.assertEqual(mr, {"iid": 20})
        self.assertIn("/projects/123/merge_requests", command)
        self.assertIn("source_branch=10-fix-bug", command)
        self.assertIn("target_branch=main", command)
        self.assertIn("squash=true", command)
        self.assertIn("remove_source_branch=true", command)
        self.assertIn("labels=bug", command)


if __name__ == "__main__":
    unittest.main()
