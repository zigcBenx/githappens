#!/usr/bin/env python3
import unittest
from unittest.mock import patch, MagicMock

from commands import create_issue


class TestCreateIssue(unittest.TestCase):
    @patch('commands.create_issue.interactive.prompt_estimated_time')
    @patch('commands.create_issue.gitlab_api.execute_issue_create')
    @patch('commands.create_issue.gitlab_api.create_branch')
    @patch('commands.create_issue.gitlab_api.create_merge_request')
    def test_run_creates_issue_branch_and_mr(
        self, mock_mr, mock_branch, mock_issue, mock_time
    ):
        mock_time.return_value = '60'
        mock_issue.return_value = {'iid': 1, 'title': 'Test'}
        mock_branch.return_value = {'name': '1-test'}
        mock_mr.return_value = {'iid': 2, 'title': 'Test', 'source_branch': '1-test'}

        result = create_issue.run(
            'Test issue', 123, 5, {'id': 10}, {'id': 20},
            {'labels': ['bug'], 'weight': 3}, False
        )

        self.assertEqual(result['iid'], 1)
        mock_issue.assert_called_once_with(
            123, 'Test issue', ['bug'], 5, {'id': 10}, {'id': 20}, 3, 60, 'issue'
        )
        mock_issue.assert_called_once()
        mock_branch.assert_called_once()
        mock_mr.assert_called_once()

    @patch('commands.create_issue.interactive.prompt_estimated_time')
    @patch('commands.create_issue.gitlab_api.execute_issue_create')
    def test_run_only_issue(self, mock_issue, mock_time):
        mock_time.return_value = ''
        mock_issue.return_value = {'iid': 1, 'title': 'Test'}

        result = create_issue.run(
            'Test issue', 123, 5, None, None,
            {'labels': ['bug']}, True
        )

        self.assertEqual(result['iid'], 1)
        mock_issue.assert_called_once_with(
            123, 'Test issue', ['bug'], 5, None, None, None, None, 'issue'
        )

    @patch('commands.create_issue.interactive.prompt_estimated_time')
    @patch('commands.create_issue.gitlab_api.execute_issue_create')
    @patch('commands.create_issue.gitlab_api.create_branch')
    @patch('commands.create_issue.gitlab_api.create_merge_request')
    def test_run_time_splitting(self, mock_mr, mock_branch, mock_issue, mock_time):
        mock_time.return_value = '120'
        mock_issue.return_value = {'iid': 1, 'title': 'Test'}
        mock_branch.return_value = {'name': '1-test'}
        mock_mr.return_value = {'iid': 2, 'title': 'Test', 'source_branch': '1-test'}

        create_issue.run(
            'Test issue', [111, 222], 5, None, None,
            {'labels': ['bug']}, False
        )

        self.assertEqual(mock_issue.call_count, 1)
        call_args = mock_issue.call_args[0]
        self.assertEqual(call_args[7], 60)  # estimated_time split across 2 projects


if __name__ == '__main__':
    unittest.main()
