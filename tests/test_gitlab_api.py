import json
import unittest
from unittest import mock

import gitlab_api


class GitlabApiTest(unittest.TestCase):
    def test_get_all_projects_success(self):
        response = mock.Mock(status_code=200, json=mock.Mock(return_value=[{"id": 1}]))
        with mock.patch("requests.get", return_value=response):
            result = gitlab_api.get_all_projects("git@gitlab.com:g/test.git")
            self.assertEqual(len(result), 1)

    def test_get_all_projects_unauthorized(self):
        response = mock.Mock(status_code=401)
        with mock.patch("requests.get", return_value=response):
            with self.assertRaises(SystemExit):
                gitlab_api.get_all_projects("git@gitlab.com:g/test.git")

    def test_create_branch_uses_issue_iid_and_main_branch(self):
        issue = {"iid": 12, "title": "Fix: Broken Thing"}
        with mock.patch(
            "subprocess.check_output",
            return_value=json.dumps({"name": "12-fix-broken-thing"}).encode(),
        ) as check_output:
            branch = gitlab_api.create_branch(99, issue)

        self.assertEqual(branch["name"], "12-fix-broken-thing")
        command = check_output.call_args.args[0]
        self.assertIn("/projects/99/repository/branches", command)
        self.assertIn("branch=12-fix-broken-thing", command)
        self.assertIn("ref=master", command)
        self.assertIn("issue_iid=12", command)

    def test_api_headers_returns_private_token(self):
        headers = gitlab_api.api_headers()
        self.assertIn("Private-Token", headers)


if __name__ == "__main__":
    unittest.main()
