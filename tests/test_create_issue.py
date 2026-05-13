import unittest

from githappens.commands.create_issue import current_milestone, slugify_branch_name


class CreateIssueTests(unittest.TestCase):
    def test_slugify_branch_name_matches_existing_format(self):
        issue = {"iid": 12, "title": "Fix: Problem (API) now"}

        self.assertEqual(slugify_branch_name(issue), "12-fix-problem-api-now")

    def test_current_milestone_selects_earliest_active_due_date(self):
        milestones = [
            {"title": "later", "start_date": "2000-01-01", "due_date": "2999-12-31"},
            {"title": "earlier", "start_date": "2000-01-01", "due_date": "2999-01-01"},
        ]

        self.assertEqual(current_milestone(milestones)["title"], "earlier")


if __name__ == "__main__":
    unittest.main()
