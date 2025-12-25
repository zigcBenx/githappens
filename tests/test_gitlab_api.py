
from unittest.mock import patch, MagicMock

import pytest
import json

from gitlab_api import (
    get_all_projects,
    get_project_id,
    list_milestones,
    get_authorized_user,
    execute_issue_create,
    get_merge_request_for_branch,
)


@patch("gitlab_api.requests.get")
@patch("gitlab_api.get_config")
def test_get_all_projects_success(mock_get_config, mock_requests_get):
    mock_config = MagicMock()
    mock_config.API_URL = "https://gitlab.com/api/v4"
    mock_config.GITLAB_TOKEN = "test_token"
    mock_get_config.return_value = mock_config

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": 1, "ssh_url_to_repo": "git@gitlab.com:test/project.git"},
        {"id": 2, "ssh_url_to_repo": "git@gitlab.com:test/other.git"},
    ]
    mock_requests_get.return_value = mock_response

    result = get_all_projects("git@gitlab.com:test/project.git")

    assert len(result) == 2
    assert result[0]["id"] == 1
    mock_requests_get.assert_called_once()
    assert "PRIVATE-TOKEN" in mock_requests_get.call_args[1]["headers"]


@patch("gitlab_api.requests.get")
@patch("gitlab_api.get_config")
def test_get_all_projects_unauthorized(mock_get_config, mock_requests_get):
    mock_config = MagicMock()
    mock_config.API_URL = "https://gitlab.com/api/v4"
    mock_config.GITLAB_TOKEN = "test_token"
    mock_get_config.return_value = mock_config

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_requests_get.return_value = mock_response

    # should exit on 401
    with pytest.raises(SystemExit):
        get_all_projects("git@gitlab.com:test/project.git")


@patch("gitlab_api.get_project_link_from_current_dir")
@patch("gitlab_api.get_all_projects")
def test_get_project_id_from_git(mock_get_all_projects, mock_get_link):
    mock_get_link.return_value = "git@gitlab.com:test/project.git"
    mock_get_all_projects.return_value = [
        {"id": 123, "ssh_url_to_repo": "git@gitlab.com:test/project.git"}
    ]

    result = get_project_id()
    assert result == 123


@patch("gitlab_api.get_project_link_from_current_dir")
def test_get_project_id_prompt_user(mock_get_link):
    mock_get_link.return_value = -1

    with patch("interactive.enter_project_id") as mock_enter:
        mock_enter.return_value = "456"
        result = get_project_id()
        assert result == "456"


@patch("gitlab_api.subprocess.run")
@patch("gitlab_api.get_config")
def test_list_milestones(mock_get_config, mock_subprocess):
    mock_config = MagicMock()
    mock_config.GROUP_ID = "123"
    mock_get_config.return_value = mock_config

    mock_result = MagicMock()
    mock_result.stdout = json.dumps(
        [{"id": 1, "title": "Milestone 1", "start_date": "2024-01-01", "due_date": "2024-12-31"}]
    )
    mock_subprocess.return_value = mock_result

    result = list_milestones()
    assert len(result) == 1
    assert result[0]["title"] == "Milestone 1"


@patch("gitlab_api.subprocess.run")
@patch("gitlab_api.get_config")
def test_list_milestones_current(mock_get_config, mock_subprocess):
    mock_config = MagicMock()
    mock_config.GROUP_ID = "123"
    mock_get_config.return_value = mock_config

    mock_result = MagicMock()
    mock_result.stdout = json.dumps(
        [{"id": 1, "title": "Current", "start_date": "2024-01-01", "due_date": "2024-12-31"}]
    )
    mock_subprocess.return_value = mock_result

    with patch("gitlab_api.datetime.date") as mock_date:
        mock_date.today.return_value.strftime.return_value = "2024-06-15"
        result = list_milestones(current=True)
        assert result["title"] == "Current"


@patch("gitlab_api.subprocess.check_output")
def test_get_authorized_user(mock_check_output):
    mock_check_output.return_value = json.dumps({"id": 1, "username": "testuser"})

    result = get_authorized_user()
    assert result["id"] == 1
    assert result["username"] == "testuser"


@patch("gitlab_api.subprocess.check_output")
@patch("gitlab_api.get_authorized_user")
def test_execute_issue_create(mock_get_user, mock_check_output):
    mock_get_user.return_value = {"id": 1}
    mock_check_output.return_value = json.dumps({"iid": 123, "title": "Test Issue"}).encode()

    result = execute_issue_create(
        project_id=1,
        title="Test Issue",
        labels=["bug"],
        milestone_id=2,
        epic=None,
        iteration=None,
        weight=5,
        estimated_time=60,
        issue_type="issue",
    )

    assert result["iid"] == 123
    assert result["title"] == "Test Issue"


@patch("gitlab_api.requests.get")
@patch("gitlab_api.get_config")
@patch("gitlab_api.get_project_id")
def test_get_merge_request_for_branch(mock_get_project_id, mock_get_config, mock_requests_get):
    mock_config = MagicMock()
    mock_config.API_URL = "https://gitlab.com/api/v4"
    mock_config.GITLAB_TOKEN = "token"
    mock_get_config.return_value = mock_config
    mock_get_project_id.return_value = 123

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"iid": 1, "source_branch": "feature-branch", "title": "Test MR"}]
    mock_requests_get.return_value = mock_response

    result = get_merge_request_for_branch("feature-branch")
    assert result["iid"] == 1
    assert result["source_branch"] == "feature-branch"
