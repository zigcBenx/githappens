from unittest.mock import patch, MagicMock

from git_utils import get_current_branch, get_main_branch, get_project_link_from_current_dir, get_two_weeks_commits


@patch("git_utils.subprocess.check_output")
def test_get_current_branch(mock_check_output):
    mock_check_output.return_value = "main"
    result = get_current_branch()
    assert result == "main"
    mock_check_output.assert_called_once_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    )


@patch("git_utils.subprocess.check_output")
def test_get_main_branch(mock_check_output):
    mock_check_output.return_value = "main"
    result = get_main_branch()
    assert result == "main"
    mock_check_output.assert_called_once()


@patch("git_utils.subprocess.run")
def test_get_project_link_from_current_dir_success(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = b"git@gitlab.com:test/project.git"
    mock_run.return_value = mock_result

    result = get_project_link_from_current_dir()
    assert result == "git@gitlab.com:test/project.git"


@patch("git_utils.subprocess.run")
def test_get_project_link_from_current_dir_failure(mock_run):
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_run.return_value = mock_result

    result = get_project_link_from_current_dir()
    assert result == -1


@patch("git_utils.subprocess.run")
def test_get_project_link_file_not_found(mock_run):
    mock_run.side_effect = FileNotFoundError()
    result = get_project_link_from_current_dir()
    assert result == -1


@patch("git_utils.subprocess.check_output")
@patch("git_utils.get_config")
def test_get_two_weeks_commits(mock_get_config, mock_check_output):
    mock_config = MagicMock()
    mock_config.DEVELOPER_EMAIL = None
    mock_get_config.return_value = mock_config

    mock_check_output.return_value = (
        "2024-01-15 - user@example.com - Fix bug\n2024-01-20 - user@example.com - Add feature"
    )

    result = get_two_weeks_commits(return_output=True)
    assert "Fix bug" in result
    assert "Add feature" in result


@patch("git_utils.subprocess.check_output")
@patch("git_utils.get_config")
def test_get_two_weeks_commits_with_email_filter(mock_get_config, mock_check_output):
    mock_config = MagicMock()
    mock_config.DEVELOPER_EMAIL = "dev@example.com"
    mock_get_config.return_value = mock_config

    mock_check_output.return_value = "2024-01-15 - dev@example.com - Fix bug"

    result = get_two_weeks_commits(return_output=True)
    assert "Fix bug" in result


@patch("git_utils.subprocess.check_output")
@patch("git_utils.get_config")
def test_get_two_weeks_commits_no_commits(mock_get_config, mock_check_output):
    mock_config = MagicMock()
    mock_config.DEVELOPER_EMAIL = None
    mock_get_config.return_value = mock_config

    mock_check_output.return_value = ""

    result = get_two_weeks_commits(return_output=True)
    assert result == ""
