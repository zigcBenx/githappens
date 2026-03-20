from unittest.mock import patch

import interactive


def test_enter_project_id_returns_input():
    with patch("builtins.input", return_value="12345"):
        assert interactive.enterProjectId() == "12345"


def test_get_project_id_when_remote_fails_uses_enter_project_id():
    with patch(
        "interactive.git_utils.getProjectLinkFromCurrentDir",
        return_value=-1,
    ):
        with patch("interactive.enterProjectId", return_value="99") as m_enter:
            assert interactive.get_project_id() == "99"
        m_enter.assert_called_once()


def test_get_project_id_resolves_from_gitlab_projects():
    link = "git@gitlab.com:g/myproj.git"
    projects = [{"id": 55, "ssh_url_to_repo": link}]
    with patch(
        "interactive.git_utils.getProjectLinkFromCurrentDir",
        return_value=link,
    ):
        with patch(
            "interactive.gitlab_api.get_all_projects",
            return_value=projects,
        ) as m_all:
            assert interactive.get_project_id() == 55
    m_all.assert_called_once_with(link)
