import unittest
from unittest.mock import patch

from githappens.main import _prompt_estimated_time_per_project


class MainTests(unittest.TestCase):
    @patch("githappens.main.prompt_estimated_time", return_value="90")
    def test_prompt_estimated_time_splits_across_projects(self, _prompt):
        self.assertEqual(_prompt_estimated_time_per_project([1, 2, 3]), 30)

    @patch("githappens.main.prompt_estimated_time", return_value="45")
    def test_prompt_estimated_time_uses_full_value_for_single_project(self, _prompt):
        self.assertEqual(_prompt_estimated_time_per_project(1), 45)

    @patch("githappens.main.prompt_estimated_time", return_value="")
    def test_prompt_estimated_time_returns_none_when_blank(self, _prompt):
        self.assertIsNone(_prompt_estimated_time_per_project([1, 2]))


if __name__ == "__main__":
    unittest.main()
