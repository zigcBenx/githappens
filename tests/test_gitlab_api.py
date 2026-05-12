import gitlab_api


def test_format_branch_name_matches_existing_cleanup():
    issue = {"iid": 42, "title": "Fix: Thing (Now)"}

    assert gitlab_api.format_branch_name(issue) == "42-fix-thing--now"


def test_build_issue_command_includes_optional_fields():
    command = gitlab_api.build_issue_command(
        project_id=123,
        title="Fix login",
        labels=["Bug", "P::1"],
        assignee_id=55,
        milestoneId=10,
        epic={"id": 7},
        iteration={"id": 9},
        weight=3,
        estimated_time=30,
    )

    assert command[:3] == ["glab", "api", "/projects/123/issues"]
    assert "title=Fix login" in command
    assert "labels=Bug,P::1" in command
    assert "milestone_id=10" in command
    assert "epic_id=7" in command
    assert "description=/iteration *iteration:9 \n/estimate 30m " in command


def test_build_merge_request_command_targets_main_branch():
    command = gitlab_api.build_merge_request_command(
        project_id=123,
        branch={"name": "42-fix-login"},
        issue={"iid": 42, "title": "Fix login"},
        labels=None,
        milestoneId=None,
        assignee_id=55,
        main_branch="main",
    )

    assert command[:3] == ["glab", "api", "/projects/123/merge_requests"]
    assert "source_branch=42-fix-login" in command
    assert "target_branch=main" in command
    assert "issue_iid=42" in command
