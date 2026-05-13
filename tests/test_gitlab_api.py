import json
import unittest
from pathlib import Path
from unittest.mock import patch

from githappens.config import AppConfig
from githappens.gitlab_api import GitLabApi


def make_config(**overrides):
    values = {
        "base_path": Path("."),
        "base_url": "https://gitlab.com",
        "api_url": "https://gitlab.com/api/v4",
        "group_id": "1",
        "custom_template": "Custom",
        "gitlab_token": "token",
        "delete_branch_after_merge": True,
        "developer_email": None,
        "squash_commits": True,
        "production_pipeline_name": "deploy",
        "production_job_name": None,
        "production_ref": None,
        "incident_project_id": None,
        "openai_api_key": None,
        "templates": [],
        "reviewers": [1],
        "production_mappings": {},
    }
    values.update(overrides)
    return AppConfig(**values)


class GitLabApiTests(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_create_merge_request_builds_expected_command(self, check_output):
        check_output.side_effect = [
            json.dumps({"id": 7}).encode(),
            json.dumps({"iid": 9, "title": "Fix bug", "source_branch": "1-fix-bug"}).encode(),
        ]
        api = GitLabApi(make_config())

        result = api.create_merge_request(
            42,
            "1-fix-bug",
            {"iid": 1, "title": "Fix bug"},
            ["bug", "P::1"],
            4,
            "main",
        )

        self.assertEqual(result["iid"], 9)
        command = check_output.call_args_list[1].args[0]
        self.assertEqual(command[:3], ["glab", "api", "/projects/42/merge_requests"])
        self.assertIn("source_branch=1-fix-bug", command)
        self.assertIn("target_branch=main", command)
        self.assertIn("labels=bug,P::1", command)
        self.assertIn("squash=true", command)
        self.assertIn("remove_source_branch=true", command)
        self.assertIn("milestone_id=4", command)


if __name__ == "__main__":
    unittest.main()
