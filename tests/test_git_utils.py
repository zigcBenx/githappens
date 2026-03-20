from unittest.mock import MagicMock, patch

import git_utils


def test_get_project_link_from_current_dir_success():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = b"git@gitlab.com:group/repo.git\n"
    with patch("git_utils.subprocess.run", return_value=mock_result):
        assert git_utils.getProjectLinkFromCurrentDir() == "git@gitlab.com:group/repo.git"


def test_get_project_link_from_current_dir_failure_code():
    mock_result = MagicMock()
    mock_result.returncode = 1
    with patch("git_utils.subprocess.run", return_value=mock_result):
        assert git_utils.getProjectLinkFromCurrentDir() == -1


def test_get_project_link_from_current_dir_file_not_found():
    with patch("git_utils.subprocess.run", side_effect=FileNotFoundError()):
        assert git_utils.getProjectLinkFromCurrentDir() == -1


def test_get_current_branch():
    with patch(
        "git_utils.subprocess.check_output",
        return_value="feature/foo\n",
    ) as m:
        assert git_utils.getCurrentBranch() == "feature/foo"
        m.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
        )


def test_get_main_branch():
    with patch(
        "git_utils.subprocess.check_output",
        return_value="main\n",
    ) as m:
        assert git_utils.getMainBranch() == "main"
        m.assert_called_once()
        args, kwargs = m.call_args
        assert kwargs.get("shell") is True
        assert "origin/HEAD" in args[0]
