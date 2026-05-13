import subprocess
import unittest
from unittest.mock import patch

from githappens import git_utils


class GitUtilsTests(unittest.TestCase):
    @patch("subprocess.check_output")
    def test_get_main_branch_uses_argv_without_shell(self, check_output):
        check_output.return_value = "refs/remotes/origin/main\n"

        self.assertEqual(git_utils.get_main_branch(), "main")
        self.assertEqual(check_output.call_args.args[0], ["git", "symbolic-ref", "refs/remotes/origin/HEAD"])
        self.assertNotIn("shell", check_output.call_args.kwargs)

    @patch("subprocess.check_output")
    def test_get_two_weeks_commits_filters_merge_commits_in_python(self, check_output):
        check_output.return_value = "\n".join(
            [
                "2026-01-01 - dev@example.com - Feature work",
                "2026-01-02 - dev@example.com - Merge branch 'main'",
            ]
        )

        result = git_utils.get_two_weeks_commits("dev@example.com")

        self.assertEqual(result, "2026-01-01 - dev@example.com - Feature work")
        command = check_output.call_args.args[0]
        self.assertIn("--author=dev@example.com", command)
        self.assertNotIn("shell", check_output.call_args.kwargs)

    @patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, ["git"]))
    def test_get_two_weeks_commits_returns_empty_string_without_matches(self, _check_output):
        self.assertEqual(git_utils.get_two_weeks_commits(), "")


if __name__ == "__main__":
    unittest.main()
