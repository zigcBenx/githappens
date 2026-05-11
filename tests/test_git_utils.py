import unittest

from githappens.git_utils import issue_branch_name


class GitUtilsTest(unittest.TestCase):
    def test_issue_branch_name_matches_existing_format(self):
        issue = {"iid": 42, "title": "Fix Thing: API (v2)"}

        self.assertEqual(issue_branch_name(issue), "42-fix-thing-api--v2")


if __name__ == "__main__":
    unittest.main()

