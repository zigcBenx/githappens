import subprocess
import unittest
from unittest.mock import Mock, patch

import git_utils


class GitUtilsTests(unittest.TestCase):
    @patch("git_utils.subprocess.run")
    def test_get_project_link_from_current_dir_returns_origin(self, run_mock):
        run_mock.return_value = Mock(returncode=0, stdout="git@gitlab.com:group/project.git\n")
        self.assertEqual(git_utils.get_project_link_from_current_dir(), "git@gitlab.com:group/project.git")

    @patch("git_utils.subprocess.check_output")
    def test_get_main_branch_strips_origin_prefix(self, check_output_mock):
        check_output_mock.return_value = "origin/main\n"
        self.assertEqual(git_utils.get_main_branch(), "main")

    @patch("git_utils.subprocess.check_output")
    def test_get_two_weeks_commits_filters_merge_commits(self, check_output_mock):
        check_output_mock.return_value = "2026-01-01 - dev@example.com - Feature\n2026-01-02 - dev@example.com - Merge branch x\n"
        result = git_utils.get_two_weeks_commits(return_output=True)
        self.assertEqual(result, "2026-01-01 - dev@example.com - Feature")


if __name__ == "__main__":
    unittest.main()
