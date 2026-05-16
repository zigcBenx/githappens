import sys
import types
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch


requests_stub = types.SimpleNamespace(get=lambda *args, **kwargs: None, put=lambda *args, **kwargs: None)
sys.modules.setdefault("requests", requests_stub)

from githappens.commands.create_issue import start_issue_creation
from githappens.commands.report import process_report


class CommandModuleTests(unittest.TestCase):
    @patch("githappens.commands.create_issue.prompt_text", return_value={"estimated_time": ""})
    @patch("githappens.commands.create_issue.create_issue", return_value={"iid": 10, "title": "Title"})
    def test_start_issue_creation_can_create_only_issue(self, create_issue, prompt_text):
        with redirect_stdout(StringIO()):
            created = start_issue_creation(1, "Title", False, False, False, {"labels": ["bug"]}, True)

        self.assertEqual(created["iid"], 10)
        create_issue.assert_called_once()

    @patch("githappens.commands.report.get_settings")
    @patch("githappens.commands.report.select_labels", return_value="Support")
    @patch("githappens.commands.report.get_active_iteration", return_value={"id": 1})
    @patch("githappens.commands.report.create_issue", return_value={"iid": 22})
    @patch("githappens.commands.report.close_opened_issue")
    @patch("subprocess.run")
    def test_report_command_creates_incident_issue_type(
        self,
        subprocess_run,
        close_opened_issue,
        create_issue,
        get_active_iteration,
        select_labels,
        get_settings,
    ):
        get_settings.return_value.incident_project_id = "99"

        with redirect_stdout(StringIO()):
            process_report("API down", 15)

        settings = create_issue.call_args.args[5]
        self.assertEqual(settings["type"], "incident")
        self.assertEqual(settings["labels"], ["incident", "report", "Support"])
        close_opened_issue.assert_called_once_with(22, "99")


if __name__ == "__main__":
    unittest.main()
