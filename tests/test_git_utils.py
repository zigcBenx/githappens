import unittest
from types import SimpleNamespace
from unittest.mock import patch

from githappens import git_utils


class GitUtilsTest(unittest.TestCase):
    def test_build_branch_name_matches_existing_slug_style(self):
        issue = {"iid": 42, "title": "Fix: Login Flow (Mobile)"}
        self.assertEqual(git_utils.build_branch_name(issue), "42-fix-login-flow--mobile")

    @patch("githappens.git_utils.subprocess.check_output")
    def test_get_two_weeks_commits_filters_merge_commits_and_developer(self, check_output):
        check_output.return_value = "\n".join(
            [
                "2026-05-01 - dev@example.test - Add feature",
                "2026-05-02 - dev@example.test - Merge branch main",
                "2026-05-03 - other@example.test - Fix bug",
            ]
        )
        ctx = SimpleNamespace(settings=SimpleNamespace(developer_email="dev@example.test"))

        output = git_utils.get_two_weeks_commits(ctx, return_output=True)

        self.assertEqual(output, "2026-05-01 - dev@example.test - Add feature")


if __name__ == "__main__":
    unittest.main()
