from commands import review


def test_get_current_issue_id_from_merge_request_description(monkeypatch):
    monkeypatch.setattr(review, "get_project_id", lambda: 123)
    monkeypatch.setattr(review, "getCurrentBranch", lambda: "feature")
    monkeypatch.setattr(
        review,
        "getMergeRequestForBranch",
        lambda project_id, branch: {"description": '"Closes #77"'},
    )

    assert review.getCurrentIssueId() == "77"
