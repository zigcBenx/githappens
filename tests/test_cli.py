import unittest

from githappens.cli import build_parser


class CliTest(unittest.TestCase):
    def test_parser_collects_title_and_flags(self):
        args = build_parser().parse_args(
            ["Fix", "login", "--only_issue", "--no_epic", "--project_id", "123"]
        )

        self.assertEqual(args.title, ["Fix", "login"])
        self.assertTrue(args.only_issue)
        self.assertTrue(args.no_epic)
        self.assertEqual(args.project_id, "123")


if __name__ == "__main__":
    unittest.main()
