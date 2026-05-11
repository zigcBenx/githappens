import unittest
from types import SimpleNamespace
from unittest.mock import patch

import git_utils


class GitUtilsTests(unittest.TestCase):
    def test_get_project_link_from_current_dir_returns_origin(self):
        with patch(
            "git_utils.subprocess.run",
            return_value=SimpleNamespace(returncode=0, stdout=b"git@gitlab.com:team/app.git\n"),
        ):
            self.assertEqual(git_utils.get_project_link_from_current_dir(), "git@gitlab.com:team/app.git")

    def test_get_project_link_from_current_dir_returns_minus_one_without_git(self):
        with patch("git_utils.subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(git_utils.get_project_link_from_current_dir(), -1)

    def test_get_current_branch_uses_git(self):
        with patch("git_utils.subprocess.check_output", return_value="feature\n") as check_output:
            self.assertEqual(git_utils.get_current_branch(), "feature")
            check_output.assert_called_once_with(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                text=True,
            )


if __name__ == "__main__":
    unittest.main()
