import interactive


def test_get_selected_milestone_by_title():
    milestones = [{"title": "Sprint 1", "id": 1}, {"title": "Sprint 2", "id": 2}]

    assert interactive.getSelectedMilestone("Sprint 2", milestones) == {"title": "Sprint 2", "id": 2}


def test_get_selected_iteration_by_date_range():
    iterations = [{"start_date": "2026-01-01", "due_date": "2026-01-14", "id": 1}]

    assert interactive.getSelectedIteration("2026-01-01 - 2026-01-14", iterations) == iterations[0]


def test_get_selected_epic_by_title():
    epics = [{"title": "Billing", "id": 7}]

    assert interactive.getSelectedEpic("Billing", epics) == epics[0]
