#!/usr/bin/env python3
import sys
import unittest
from unittest.mock import patch, MagicMock

import main


class TestMain(unittest.TestCase):
    @patch('main._parser.print_help')
    @patch.object(sys, 'argv', ['main.py'])
    def test_no_args_shows_help(self, mock_help):
        with self.assertRaises(SystemExit) as ctx:
            main.main()
        self.assertEqual(ctx.exception.code, 1)
        mock_help.assert_called_once()

    @patch('commands.open_mr.run')
    @patch.object(sys, 'argv', ['main.py', 'open'])
    def test_open_command(self, mock_open_mr):
        main.main()
        mock_open_mr.assert_called_once()

    @patch('commands.review.run')
    @patch.object(sys, 'argv', ['main.py', 'review'])
    def test_review_command(self, mock_review):
        main.main()
        mock_review.assert_called_once_with(auto_merge=False, select_reviewers=False)

    @patch('commands.review.run')
    @patch.object(sys, 'argv', ['main.py', 'review', '--auto_merge', '--select'])
    def test_review_with_flags(self, mock_review):
        main.main()
        mock_review.assert_called_once_with(auto_merge=True, select_reviewers=True)

    @patch('commands.summary.run')
    @patch.object(sys, 'argv', ['main.py', 'summary'])
    def test_summary_command(self, mock_summary):
        main.main()
        mock_summary.assert_called_once_with(ai=False)

    @patch('commands.summary.run')
    @patch.object(sys, 'argv', ['main.py', 'summaryAI'])
    def test_summary_ai_command(self, mock_summary):
        main.main()
        mock_summary.assert_called_once_with(ai=True)

    @patch('commands.deploy.run')
    @patch.object(sys, 'argv', ['main.py', 'last', 'deploy'])
    def test_deploy_command(self, mock_deploy):
        main.main()
        mock_deploy.assert_called_once()

    @patch('commands.report.run')
    @patch.object(sys, 'argv', ['main.py', 'report', 'incident', '30'])
    def test_report_command(self, mock_report):
        main.main()
        mock_report.assert_called_once_with('incident', 30)

    @patch('gitlab_api.get_project_id')
    @patch('commands.create_issue.run')
    @patch('main.templates.select_template')
    @patch('main.templates.get_issue_settings')
    @patch('main.interactive.get_milestone')
    @patch('main.interactive.get_iteration')
    @patch('main.interactive.get_epic')
    @patch('main.git_utils.get_main_branch')
    @patch.object(sys, 'argv', ['main.py', 'My', 'Issue'])
    def test_issue_creation(self, mock_branch, mock_epic, mock_iter, mock_milestone, mock_settings, mock_select, mock_create, mock_pid):
        mock_pid.return_value = '12345'
        mock_select.return_value = 'Bug easy'
        mock_settings.return_value = {'labels': ['Bug'], 'weight': 1}
        mock_milestone.return_value = {'id': 5}
        mock_iter.return_value = {'id': 10}
        mock_epic.return_value = {'id': 20}
        mock_branch.return_value = 'master'
        mock_create.return_value = {'iid': 1}

        main.main()
        mock_create.assert_called_once()
        mock_create.assert_called_once_with(
            'My Issue',
            '12345',
            5,
            {'id': 20},
            {'id': 10},
            {'labels': ['Bug'], 'weight': 1},
            False,
        )


if __name__ == '__main__':
    unittest.main()
