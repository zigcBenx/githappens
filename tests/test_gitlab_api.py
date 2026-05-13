import json
import unittest
from unittest import mock

from githappens import gitlab_api


class GitlabApiTest(unittest.TestCase):
    def test_create_branch_uses_issue_iid_and_main_branch(self):
        issue = {"iid": 12, "title": "Fix: Broken Thing"}

        with mock.patch("subprocess.check_output", return_value=json.dumps({"name": "12-fix-broken-thing"}).encode()) as check_output:
            branch = gitlab_api.create_branch(99, issue, "main")

        self.assertEqual(branch["name"], "12-fix-broken-thing")
        command = check_output.call_args.args[0]
        self.assertIn("/projects/99/repository/branches", command)
        self.assertIn("branch=12-fix-broken-thing", command)
        self.assertIn("ref=main", command)
        self.assertIn("issue_iid=12", command)

    def test_create_issue_includes_estimate_in_description(self):
        with mock.patch("githappens.gitlab_api.get_authorized_user", return_value={"id": 7}), \
             mock.patch("subprocess.check_output", return_value=json.dumps({"iid": 3}).encode()) as check_output:
            gitlab_api.create_issue(
                11,
                "Title",
                ["Bug", "P::1"],
                22,
                {"id": 33},
                {"id": 44},
                5,
                90,
            )

        command = check_output.call_args.args[0]
        self.assertIn("labels=Bug,P::1", command)
        self.assertIn("milestone_id=22", command)
        self.assertIn("epic_id=33", command)
        self.assertIn("description=/iteration *iteration:44 \n/estimate 90m ", command)


if __name__ == "__main__":
    unittest.main()
