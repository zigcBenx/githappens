import unittest
from unittest.mock import Mock

from githappens.commands.create_issue import current_milestone, get_active_iteration, slugify_branch_name


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

    def test_current_milestone_returns_none_without_active_milestone(self):
        milestones = [
            {"title": "past", "start_date": "2000-01-01", "due_date": "2000-01-31"},
            {"title": "missing dates", "start_date": None, "due_date": None},
        ]

        self.assertIsNone(current_milestone(milestones))

    def test_get_active_iteration_returns_none_without_active_iteration(self):
        api = Mock()
        api.list_group_iterations.return_value = [
            {"id": 1, "start_date": "2000-01-01", "due_date": "2000-01-31"},
            {"id": 2, "start_date": None, "due_date": None},
        ]

        self.assertIsNone(get_active_iteration(api))


if __name__ == "__main__":
    unittest.main()
