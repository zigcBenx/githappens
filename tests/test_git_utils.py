#!/usr/bin/env python3
import unittest
from unittest.mock import patch, MagicMock

import git_utils


class TestGitUtils(unittest.TestCase):
    @patch('git_utils.subprocess.run')
    def test_get_project_link_from_current_dir_success(self, mock_run):
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b'git@gitlab.com:user/repo.git\n'
        result = git_utils.get_project_link_from_current_dir()
        self.assertEqual(result, 'git@gitlab.com:user/repo.git')

    @patch('git_utils.subprocess.run')
    def test_get_project_link_from_current_dir_failure(self, mock_run):
        mock_run.return_value.returncode = 1
        result = git_utils.get_project_link_from_current_dir()
        self.assertEqual(result, -1)

    @patch('git_utils.subprocess.check_output')
    def test_get_current_branch(self, mock_output):
        mock_output.return_value = 'feature-branch\n'
        result = git_utils.get_current_branch()
        self.assertEqual(result, 'feature-branch')

    @patch('git_utils.subprocess.check_output')
    def test_get_main_branch(self, mock_output):
        mock_output.return_value = 'master\n'
        result = git_utils.get_main_branch()
        self.assertEqual(result, 'master')

    @patch('git_utils.subprocess.check_output')
    def test_get_two_weeks_commits(self, mock_output):
        mock_output.return_value = '2024-01-01 - user@example.com - commit msg\n'
        result = git_utils.get_two_weeks_commits(return_output=True)
        self.assertIn('commit msg', result)

    @patch('git_utils.webbrowser.open')
    @patch('git_utils.subprocess.check_output')
    @patch('gitlab_api.get_active_merge_request_id')
    def test_open_merge_request_in_browser(self, mock_mr_id, mock_git, mock_open_browser):
        mock_mr_id.return_value = 5
        mock_git.return_value = 'git@gitlab.com:user/repo.git\n'
        git_utils.open_merge_request_in_browser()
        mock_open_browser.assert_called_once()


if __name__ == '__main__':
    unittest.main()
