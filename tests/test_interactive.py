import unittest

from githappens import interactive


class InteractiveSelectionTest(unittest.TestCase):
    def test_selected_milestone_iteration_and_epic_match_labels(self):
        milestones = [{"id": 1, "title": "Sprint 1"}, {"id": 2, "title": "Sprint 2"}]
        iterations = [
            {"id": 3, "start_date": "2026-05-01", "due_date": "2026-05-15"},
            {"id": 4, "start_date": "2026-05-16", "due_date": "2026-05-31"},
        ]
        epics = [{"id": 5, "title": "Checkout"}, {"id": 6, "title": "Login"}]

        self.assertEqual(
            interactive.get_selected_milestone("Sprint 2", milestones),
            {"id": 2, "title": "Sprint 2"},
        )
        self.assertEqual(
            interactive.get_selected_iteration("2026-05-01 - 2026-05-15", iterations),
            {"id": 3, "start_date": "2026-05-01", "due_date": "2026-05-15"},
        )
        self.assertEqual(
            interactive.get_selected_epic("Checkout", epics),
            {"id": 5, "title": "Checkout"},
        )


if __name__ == "__main__":
    unittest.main()
