from commands import open_mr


def test_find_merge_request_id_by_branch(monkeypatch):
    monkeypatch.setattr(open_mr, "get_project_id", lambda: 123)
    monkeypatch.setattr(
        open_mr,
        "getMergeRequestForBranch",
        lambda project_id, branch: {"iid": 9, "source_branch": branch},
    )

    assert open_mr.find_merge_request_id_by_branch("feature") == 9
