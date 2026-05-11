import io
import types
import unittest
from contextlib import redirect_stdout
from unittest import mock

from githappens.main import main


class AppTests(unittest.TestCase):
    def test_report_invalid_minutes_keeps_friendly_message(self):
        runtime = types.SimpleNamespace(config=types.SimpleNamespace())

        output = io.StringIO()
        with mock.patch("githappens.main.load_runtime", return_value=runtime):
            with mock.patch("githappens.main.get_main_branch", return_value="master"):
                with mock.patch("githappens.main.GitLabClient.from_config", return_value=mock.Mock()):
                    with redirect_stdout(output):
                        status = main(["report", "incident", "abc"])

        self.assertEqual(status, 1)
        self.assertIn("Invalid minutes. Please provide a valid number.", output.getvalue())
