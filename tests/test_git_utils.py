import subprocess
import unittest
from unittest.mock import Mock, patch

from git_utils import get_current_branch, get_project_link_from_current_dir


class GitUtilsTests(unittest.TestCase):
    @patch("git_utils.subprocess.run")
    def test_get_project_link_from_current_dir_returns_remote_url(self, run):
        run.return_value = Mock(returncode=0, stdout=b"git@gitlab.com:group/repo.git\n")

        self.assertEqual(get_project_link_from_current_dir(), "git@gitlab.com:group/repo.git")

    @patch("git_utils.subprocess.run", side_effect=FileNotFoundError)
    def test_get_project_link_from_current_dir_handles_missing_git(self, _run):
        self.assertEqual(get_project_link_from_current_dir(), -1)

    @patch("git_utils.subprocess.check_output", return_value="feature\n")
    def test_get_current_branch_strips_output(self, check_output):
        self.assertEqual(get_current_branch(), "feature")
        check_output.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
