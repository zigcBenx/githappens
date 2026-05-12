import unittest

from interactive import get_selected_epic, get_selected_iteration, get_selected_milestone


class InteractiveTests(unittest.TestCase):
    def test_get_selected_milestone_returns_matching_item(self):
        milestones = [{"title": "Sprint 1"}, {"title": "Sprint 2"}]

        self.assertEqual(get_selected_milestone("Sprint 2", milestones), {"title": "Sprint 2"})

    def test_get_selected_iteration_matches_date_range_label(self):
        iterations = [
            {"id": 1, "start_date": "2026-01-01", "due_date": "2026-01-15"},
            {"id": 2, "start_date": "2026-01-16", "due_date": "2026-01-31"},
        ]

        self.assertEqual(
            get_selected_iteration("2026-01-16 - 2026-01-31", iterations),
            {"id": 2, "start_date": "2026-01-16", "due_date": "2026-01-31"},
        )

    def test_get_selected_epic_returns_matching_item(self):
        epics = [{"title": "Platform"}, {"title": "Billing"}]

        self.assertEqual(get_selected_epic("Billing", epics), {"title": "Billing"})


if __name__ == "__main__":
    unittest.main()
