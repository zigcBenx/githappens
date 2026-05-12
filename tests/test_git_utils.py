import subprocess
import unittest
from unittest.mock import Mock, patch

import git_utils


class GitUtilsTests(unittest.TestCase):
    def test_get_project_link_from_current_dir_returns_remote(self):
        result = Mock(returncode=0, stdout=b"git@gitlab.com:group/project.git\n")

        with patch("git_utils.subprocess.run", return_value=result):
            self.assertEqual(git_utils.get_project_link_from_current_dir(), "git@gitlab.com:group/project.git")

    def test_get_project_link_from_current_dir_returns_minus_one_without_git_remote(self):
        result = Mock(returncode=1, stdout=b"")

        with patch("git_utils.subprocess.run", return_value=result):
            self.assertEqual(git_utils.get_project_link_from_current_dir(), -1)

    def test_get_two_weeks_commits_returns_output(self):
        with patch("git_utils.subprocess.check_output", return_value="2026-05-12 - dev@example.com - Add tests\n"):
            output = git_utils.get_two_weeks_commits(return_output=True, developer_email=None)

        self.assertIn("Add tests", output)

    def test_get_two_weeks_commits_returns_empty_on_git_error(self):
        with patch("git_utils.subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "git")), \
                patch("builtins.print"):
            output = git_utils.get_two_weeks_commits(return_output=True, developer_email=None)

        self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
