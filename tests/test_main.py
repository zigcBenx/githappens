import unittest
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_parser_accepts_review_select(self):
        args = main.build_parser().parse_args(["review", "--select"])

        self.assertEqual(args.title, ["review"])
        self.assertTrue(args.select)

    def test_main_routes_summary_without_prompts(self):
        with patch("main.git_utils.get_two_weeks_commits") as commits:
            main.main(["summary"])

        commits.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
