from unittest.mock import MagicMock, patch

import gitlab_api


def test_get_all_projects_makes_correct_api_call():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"id": 1, "name": "repo"}]
    with patch("gitlab_api.requests.get", return_value=mock_resp) as m_get:
        out = gitlab_api.get_all_projects("git@gitlab.com:acme/my.repo.git")
    assert out == [{"id": 1, "name": "repo"}]
    m_get.assert_called_once()
    url, kwargs = m_get.call_args[0][0], m_get.call_args[1]
    assert url.endswith("/projects?membership=true&search=my")
    assert kwargs["headers"]["PRIVATE-TOKEN"] == "test-token"


def test_get_merge_request_for_branch_uses_correct_url():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {"source_branch": "other", "iid": 1},
        {"source_branch": "feat-x", "iid": 2},
    ]
    with patch("gitlab_api.requests.get", return_value=mock_resp) as m_get:
        mr = gitlab_api.getMergeRequestForBranch(42, "feat-x")
    assert mr["iid"] == 2
    m_get.assert_called_once()
    url = m_get.call_args[0][0]
    assert url == "https://gitlab.test/api/v4/projects/42/merge_requests"
    assert m_get.call_args[1]["params"] == {"source_branch": "feat-x"}
    assert m_get.call_args[1]["headers"]["Private-Token"] == "test-token"


def test_add_reviewers_to_merge_request_sends_correct_data():
    mock_put = MagicMock()
    with patch("gitlab_api.requests.put", mock_put):
        gitlab_api.addReviewersToMergeRequest(7, 11, reviewers=[3, 4])
    mock_put.assert_called_once()
    assert mock_put.call_args[0][0].endswith(
        "/projects/7/merge_requests/11"
    )
    assert mock_put.call_args[1]["json"] == {"reviewer_ids": [3, 4]}
    assert mock_put.call_args[1]["headers"]["Private-Token"] == "test-token"


def test_set_merge_request_to_auto_merge_sends_correct_data():
    mock_put = MagicMock()
    with patch("gitlab_api.requests.put", mock_put):
        gitlab_api.setMergeRequestToAutoMerge(7, 11)
    mock_put.assert_called_once()
    assert mock_put.call_args[0][0].endswith(
        "/projects/7/merge_requests/11/merge"
    )
    assert mock_put.call_args[1]["json"] == {
        "id": 7,
        "merge_request_iid": 11,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
