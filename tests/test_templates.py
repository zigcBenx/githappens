#!/usr/bin/env python3
import unittest
from unittest.mock import patch, MagicMock

import templates


class TestTemplates(unittest.TestCase):
    @patch('templates.config.TEMPLATES', [
        {'name': 'Bug easy', 'weight': 1, 'labels': ['Bug']},
        {'name': 'Feature', 'weight': 3, 'labels': ['feature::Confirmed']},
    ])
    @patch('templates.config.CUSTOM_TEMPLATE', 'Custom')
    @patch('inquirer.prompt')
    def test_select_template(self, mock_prompt):
        mock_prompt.return_value = {'template': 'Bug easy'}
        result = templates.select_template()
        self.assertEqual(result, 'Bug easy')

    @patch('templates.config.TEMPLATES', [
        {'name': 'Bug easy', 'weight': 1, 'labels': ['Bug']},
    ])
    @patch('templates.config.CUSTOM_TEMPLATE', 'Custom')
    def test_get_issue_settings_found(self):
        result = templates.get_issue_settings('Bug easy')
        self.assertEqual(result['weight'], 1)

    @patch('templates.config.TEMPLATES', [])
    @patch('templates.config.CUSTOM_TEMPLATE', 'Custom')
    def test_get_issue_settings_custom(self):
        result = templates.get_issue_settings('Custom')
        self.assertEqual(result, {})

    @patch('templates.config.TEMPLATES', [])
    @patch('templates.config.CUSTOM_TEMPLATE', 'Custom')
    def test_get_issue_settings_not_found(self):
        result = templates.get_issue_settings('Missing')
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
