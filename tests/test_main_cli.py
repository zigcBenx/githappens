import unittest
from unittest import mock

from githappens import main


class MainCliTest(unittest.TestCase):
    def test_open_routes_to_open_merge_request_command(self):
        with mock.patch("githappens.main.open_merge_request_in_browser") as open_mr:
            main.main(["open"])

        open_mr.assert_called_once_with()

    def test_review_routes_to_review_flow(self):
        with mock.patch("githappens.main.review_flow") as review_flow:
            main.main(["review", "--select", "--auto_merge"])

        review_flow.assert_called_once_with(auto_merge=True, select=True)

    def test_report_validates_minutes(self):
        with mock.patch("githappens.main.process_report") as process_report:
            main.main(["report", "Outage", "15"])

        process_report.assert_called_once_with("Outage", 15)


if __name__ == "__main__":
    unittest.main()
