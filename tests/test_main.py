import unittest

from main import build_parser


class MainTests(unittest.TestCase):
    def test_build_parser_supports_review_flags(self):
        args = build_parser().parse_args(["review", "--select", "-am"])

        self.assertEqual(args.title, ["review"])
        self.assertTrue(args.select)
        self.assertTrue(args.auto_merge)


if __name__ == "__main__":
    unittest.main()
