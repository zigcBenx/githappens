import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from githappens.main import build_parser, main


class MainEntrypointTests(unittest.TestCase):
    def test_parser_keeps_existing_flags(self):
        parser = build_parser()
        args = parser.parse_args(["review", "--select", "--auto_merge"])

        self.assertEqual(args.title, ["review"])
        self.assertTrue(args.select)
        self.assertTrue(args.auto_merge)

    def test_help_does_not_require_runtime_config(self):
        output = io.StringIO()

        with self.assertRaises(SystemExit) as context, redirect_stdout(output):
            main(["--help"])

        self.assertEqual(context.exception.code, 0)
        self.assertIn("--only_issue", output.getvalue())

    def test_invalid_report_minutes_is_handled(self):
        output = io.StringIO()

        with redirect_stdout(output):
            main(["report", "Something happened", "not-a-number"])

        self.assertIn("Invalid minutes", output.getvalue())

    @patch("githappens.commands.open_mr.open_merge_request_in_browser")
    def test_open_command_dispatches_to_command_module(self, open_merge_request):
        main(["open"])

        open_merge_request.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
