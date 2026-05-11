import unittest

from githappens.gitlab_api import _append_field, _slugify_branch_title


class GitlabApiHelpersTest(unittest.TestCase):
    def test_slugify_branch_title_matches_cli_branch_style(self):
        self.assertEqual(
            _slugify_branch_title("Fix: API (Auth) flow"),
            "fix-api--auth-flow",
        )

    def test_append_field_skips_empty_values(self):
        command = ["glab", "api"]
        _append_field(command, "labels", "")
        self.assertEqual(command, ["glab", "api"])

    def test_append_field_adds_glab_field_pair(self):
        command = ["glab", "api"]
        _append_field(command, "labels", "bug")
        self.assertEqual(command, ["glab", "api", "-f", "labels=bug"])


if __name__ == "__main__":
    unittest.main()
