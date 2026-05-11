import unittest
from unittest.mock import patch

import interactive


class InteractiveTests(unittest.TestCase):
    @patch("interactive.templates.TEMPLATES", [{"name": "Bug"}])
    @patch("interactive.inquirer.prompt")
    def test_select_template_returns_prompt_value(self, prompt_mock):
        prompt_mock.return_value = {"template": "Bug"}
        self.assertEqual(interactive.select_template(), "Bug")

    @patch("interactive.inquirer.prompt")
    def test_choose_reviewers_manually_casts_ids_to_ints(self, prompt_mock):
        prompt_mock.return_value = {"selected_reviewers": ["1", "2"]}
        self.assertEqual(interactive.choose_reviewers_manually([("A", 1), ("B", 2)]), [1, 2])


if __name__ == "__main__":
    unittest.main()
