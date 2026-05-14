import unittest
from unittest import mock

import main


class MainCliTest(unittest.TestCase):
    def test_main_routes_open_command(self):
        with mock.patch("main.openMergeRequestInBrowser") as open_mr:
            with mock.patch.object(main.sys, "argv", ["gitHappens.py", "open"]):
                try:
                    main.main()
                except SystemExit:
                    pass
            open_mr.assert_called_once()

    def test_main_routes_summary_command(self):
        with mock.patch("main.get_two_weeks_commits") as commits:
            with mock.patch.object(main.sys, "argv", ["gitHappens.py", "summary"]):
                try:
                    main.main()
                except SystemExit:
                    pass
            commits.assert_called_once()

    def test_main_routes_deploy_command(self):
        with mock.patch("main.process_report") as report:
            with mock.patch.object(main.sys, "argv", ["gitHappens.py", "report", "test incident", "30"]):
                try:
                    main.main()
                except SystemExit:
                    pass
            report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
