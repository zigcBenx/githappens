import types
import sys
import unittest
from unittest import mock

from githappens.gitlab_api import GitLabApiError, GitLabClient


class GitLabClientTests(unittest.TestCase):
    def test_request_translates_unauthorized_response(self):
        client = GitLabClient("https://gitlab.example.com", "https://gitlab.example.com/api/v4", "1", "token")
        response = types.SimpleNamespace(status_code=401, ok=False, text="Unauthorized")
        fake_requests = types.SimpleNamespace(request=mock.Mock(return_value=response))

        with mock.patch.dict(sys.modules, {"requests": fake_requests}):
            with self.assertRaisesRegex(GitLabApiError, "Unauthorized"):
                client._request("GET", "/projects")

    def test_create_branch_uses_legacy_branch_name_builder(self):
        client = GitLabClient("https://gitlab.example.com", "https://gitlab.example.com/api/v4", "1", "token")

        with mock.patch.object(client, "_glab_json", return_value={"name": "123-fix-api/client_v2-path"}) as glab:
            branch = client.create_branch(
                456,
                {"iid": 123, "title": "Fix API/client_v2 path"},
                "master",
            )

        self.assertEqual(branch["name"], "123-fix-api/client_v2-path")
        self.assertIn("branch=123-fix-api/client_v2-path", glab.call_args.args)
