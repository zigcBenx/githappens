from commands import create_issue


def test_get_project_id_matches_current_remote(monkeypatch):
    monkeypatch.setattr(create_issue, "getProjectLinkFromCurrentDir", lambda: "git@gitlab.com:org/app.git")
    monkeypatch.setattr(
        create_issue,
        "get_all_projects",
        lambda project_link: [{"ssh_url_to_repo": "git@gitlab.com:org/app.git", "id": 123}],
    )

    assert create_issue.get_project_id() == 123


def test_get_project_id_prompts_when_not_in_git_repo(monkeypatch):
    monkeypatch.setattr(create_issue, "getProjectLinkFromCurrentDir", lambda: -1)
    monkeypatch.setattr(create_issue, "enterProjectId", lambda: "456")

    assert create_issue.get_project_id() == "456"
