import pytest

from interactive import (
    get_selected_milestone,
    get_selected_epic,
    get_selected_iteration,
)


class TestInteractive:

    def test_get_selected_milestone(self):
        milestones = [
            {"title": "Milestone 1", "id": 1},
            {"title": "Milestone 2", "id": 2},
        ]
        result = get_selected_milestone("Milestone 1", milestones)
        assert result["id"] == 1
        assert result["title"] == "Milestone 1"

    def test_get_selected_milestone_not_found(self):
        milestones = [{"title": "Milestone 1", "id": 1}]
        result = get_selected_milestone("NonExistent", milestones)
        assert result is None

    def test_get_selected_epic(self):
        epics = [
            {"title": "Epic 1", "id": 1},
            {"title": "Epic 2", "id": 2},
        ]
        result = get_selected_epic("Epic 1", epics)
        assert result["id"] == 1
        assert result["title"] == "Epic 1"

    def test_get_selected_epic_not_found(self):
        epics = [{"title": "Epic 1", "id": 1}]
        result = get_selected_epic("NonExistent", epics)
        assert result is None

    def test_get_selected_iteration(self):
        iterations = [
            {"start_date": "2025-01-01", "due_date": "2025-01-31", "id": 1},
            {"start_date": "2025-02-01", "due_date": "2025-02-28", "id": 2},
        ]
        result = get_selected_iteration("2025-01-01 - 2025-01-31", iterations)
        assert result["id"] == 1

    def test_get_selected_iteration_not_found(self):
        iterations = [
            {"start_date": "2025-01-01", "due_date": "2025-01-31", "id": 1}
        ]
        result = get_selected_iteration("2025-02-01 - 2025-02-28", iterations)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
