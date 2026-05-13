import unittest
from unittest import mock

from githappens.commands import review


class ReviewCommandTest(unittest.TestCase):
    def test_current_issue_id_reads_closes_reference(self):
        with mock.patch("githappens.commands.review.git_utils.get_current_branch", return_value="12-fix"), \
             mock.patch(
                 "githappens.commands.review.get_merge_request_for_branch",
                 return_value={"description": '"Closes #42"'},
             ):
            self.assertEqual(review.get_current_issue_id(), "42")

    def test_current_issue_id_errors_when_merge_request_is_missing(self):
        with mock.patch("githappens.commands.review.git_utils.get_current_branch", return_value="12-fix"), \
             mock.patch("githappens.commands.review.get_merge_request_for_branch", return_value=None):
            with self.assertRaises(ValueError):
                review.get_current_issue_id()


if __name__ == "__main__":
    unittest.main()
