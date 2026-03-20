from unittest.mock import MagicMock, patch

from commands import create_issue, deploy, summary


def test_create_issue_calls_execute_issue_create():
    settings = {
        "type": "issue",
        "labels": ["a"],
        "weight": 2,
        "estimated_time": 30,
    }
    mock_execute = MagicMock(return_value={"iid": 1, "title": "t"})
    with patch("commands.create_issue.gitlab_api.executeIssueCreate", mock_execute):
        create_issue.createIssue(
            "My title",
            10,
            milestoneId=5,
            epic=None,
            iteration=None,
            settings=settings,
        )
    mock_execute.assert_called_once_with(
        10,
        "My title",
        ["a"],
        5,
        None,
        None,
        2,
        30,
        "issue",
    )


def test_get_last_production_deploy_calls_gitlab_api():
    fake_result = {
        "pipeline": {
            "id": 1,
            "status": "success",
            "ref": "main",
            "sha": "abcdef12",
            "web_url": "https://example/pipeline",
        },
        "production_job": {
            "name": "deploy",
            "status": "success",
            "started_at": "2020-01-01T00:00:00Z",
            "finished_at": "2020-01-01T00:05:00Z",
            "duration": 120,
        },
    }
    with patch(
        "commands.deploy.interactive.get_project_id",
        return_value=77,
    ) as m_pid:
        with patch(
            "commands.deploy.gitlab_api.get_last_production_deploy_info",
            return_value=fake_result,
        ) as m_info:
            with patch("commands.deploy.print"):
                deploy.get_last_production_deploy()
    m_pid.assert_called_once()
    m_info.assert_called_once_with(77, ref="master")


def test_get_two_weeks_commits_with_mocked_subprocess():
    fake_log = "2024-01-01 - dev@x.com - fix thing"
    with patch(
        "commands.summary.subprocess.check_output",
        return_value=fake_log,
    ) as m_co:
        with patch("commands.summary.print"):
            out = summary.get_two_weeks_commits(return_output=True)
    assert out == fake_log
    m_co.assert_called_once()
    call_kw = m_co.call_args[1]
    assert call_kw.get("shell") is True
    assert "git log --since=" in m_co.call_args[0][0]
