import json
import sys
import types
import unittest
from unittest.mock import patch


requests_stub = types.SimpleNamespace(get=lambda *args, **kwargs: None, put=lambda *args, **kwargs: None)
sys.modules.setdefault("requests", requests_stub)

from githappens import gitlab_api


class GitlabApiTests(unittest.TestCase):
    def test_execute_issue_create_passes_issue_type(self):
        with patch.object(gitlab_api, "get_authorized_user", return_value={"id": 7}), patch(
            "subprocess.check_output", return_value=json.dumps({"iid": 5}).encode()
        ) as check_output:
            issue = gitlab_api.execute_issue_create(
                project_id=123,
                title="Incident Report",
                labels=["incident", "report"],
                milestone_id=False,
                epic=False,
                iteration={"id": 9},
                weight=None,
                estimated_time=30,
                issue_type="incident",
            )

        command = check_output.call_args.args[0]
        self.assertEqual(issue["iid"], 5)
        self.assertIn("issue_type=incident", command)
        self.assertIn("labels=incident,report", command)
        self.assertIn("description=/iteration *iteration:9 \n/estimate 30m ", command)

    def test_create_branch_keeps_original_branch_name_format(self):
        with patch("subprocess.check_output", return_value=json.dumps({"name": "12-fix-it"}).encode()) as check_output:
            branch = gitlab_api.create_branch(1, {"iid": 12, "title": "Fix: It"})

        command = check_output.call_args.args[0]
        self.assertEqual(branch["name"], "12-fix-it")
        self.assertIn("branch=12-fix-it", command)


if __name__ == "__main__":
    unittest.main()
