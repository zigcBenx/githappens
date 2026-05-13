import configparser
import unittest
from unittest import mock

from githappens.commands import report


class ReportCommandTest(unittest.TestCase):
    def test_report_returns_when_incident_project_is_missing(self):
        missing_option = configparser.NoOptionError("incident_project_id", "DEFAULT")

        with mock.patch("githappens.commands.report.config.config.get", side_effect=missing_option), \
             mock.patch("githappens.commands.report.create_issue") as create_issue, \
             mock.patch("builtins.print"):
            report.process_report("API outage", 15)

        create_issue.assert_not_called()

    def test_report_creates_incident_and_tracks_time(self):
        with mock.patch("githappens.commands.report.config.config.get", return_value="99"), \
             mock.patch("githappens.commands.report.select_labels", return_value="Department::SRE"), \
             mock.patch("githappens.commands.report.get_active_iteration", return_value={"id": 5}), \
             mock.patch("githappens.commands.report.create_issue", return_value={"iid": 12}) as create_issue, \
             mock.patch("githappens.commands.report.close_opened_issue") as close_opened_issue, \
             mock.patch("githappens.commands.report.subprocess.run") as run, \
             mock.patch("builtins.print"):
            report.process_report("API outage", 15)

        create_issue.assert_called_once()
        args = create_issue.call_args.args
        self.assertEqual(args[0], "Incident Report: API outage")
        self.assertEqual(args[1], "99")
        self.assertEqual(args[4], {"id": 5})
        self.assertEqual(
            args[5],
            {
                "labels": ["incident", "report", "Department::SRE"],
                "onlyIssue": True,
                "type": "incident",
            },
        )
        close_opened_issue.assert_called_once_with(12, "99")
        run.assert_called_once()
        self.assertIn("/projects/99/issues/12/add_spent_time", run.call_args.args[0])
        self.assertIn("duration=15m", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
