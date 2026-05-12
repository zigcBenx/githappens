#!/usr/bin/env python3
import json
import unittest
from unittest.mock import patch, MagicMock

import gitlab_api


class TestGitlabApi(unittest.TestCase):
    @patch('gitlab_api.subprocess.check_output')
    def test_get_authorized_user(self, mock_output):
        mock_output.return_value = json.dumps({'id': 1, 'username': 'test'}).encode()
        result = gitlab_api.get_authorized_user()
        self.assertEqual(result['id'], 1)
        mock_output.assert_called_once_with(["glab", "api", "/user"])

    @patch('gitlab_api.requests.get')
    def test_api_get_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{'id': 1}]
        result = gitlab_api._api_get('/projects')
        self.assertEqual(result, [{'id': 1}])

    @patch('gitlab_api.requests.get')
    def test_api_get_401(self, mock_get):
        mock_get.return_value.status_code = 401
        with self.assertRaises(SystemExit):
            gitlab_api._api_get('/projects')

    @patch('gitlab_api.requests.put')
    def test_api_put(self, mock_put):
        mock_put.return_value.status_code = 200
        response = gitlab_api._api_put('/projects/1/merge_requests/2', json_data={'foo': 'bar'})
        self.assertEqual(response.status_code, 200)

    @patch('gitlab_api.requests.post')
    def test_post_to_merge_request(self, mock_post):
        mock_post.return_value.status_code = 201
        result = gitlab_api.post_to_merge_request('body', 1, 2)
        self.assertTrue(result)

    @patch('gitlab_api.requests.post')
    def test_post_inline_comment(self, mock_post):
        mock_post.return_value.status_code = 201
        result = gitlab_api.post_inline_comment(
            1, 2, 'body text', {'base_sha': 'a', 'head_sha': 'b', 'start_sha': 'c'}, 'file.py', 10
        )
        self.assertTrue(result)

    @patch('gitlab_api.requests.get')
    def test_get_diff_refs(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'diff_refs': {'base_sha': 'a', 'head_sha': 'b', 'start_sha': 'c'}
        }
        result = gitlab_api.get_diff_refs(1, 2)
        self.assertEqual(result, {'base_sha': 'a', 'head_sha': 'b', 'start_sha': 'c'})

    @patch('gitlab_api.requests.get')
    def test_get_merge_request_changes(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'changes': []}
        result = gitlab_api.get_merge_request_changes(1, 2)
        self.assertEqual(result, {'changes': []})

    @patch('gitlab_api.get_authorized_user')
    @patch('gitlab_api.subprocess.check_output')
    def test_execute_issue_create(self, mock_output, mock_user):
        mock_user.return_value = {'id': 99}
        mock_output.return_value = json.dumps({'iid': 42, 'title': 'Test'}).encode()
        result = gitlab_api.execute_issue_create(
            1, 'Test', ['bug'], 5, None, None, 3, 60, 'issue'
        )
        self.assertEqual(result['iid'], 42)

    @patch('gitlab_api.subprocess.check_output')
    def test_create_branch(self, mock_output):
        mock_output.return_value = json.dumps({'name': '42-test-branch'}).encode()
        result = gitlab_api.create_branch(1, {'iid': 42, 'title': 'Test issue'})
        self.assertEqual(result['name'], '42-test-branch')

    @patch('gitlab_api.get_authorized_user')
    @patch('gitlab_api.subprocess.check_output')
    def test_create_merge_request(self, mock_output, mock_user):
        mock_user.return_value = {'id': 99}
        mock_output.return_value = json.dumps({'iid': 10, 'title': 'Test'}).encode()
        result = gitlab_api.create_merge_request(
            1, {'name': 'branch'}, {'iid': 1, 'title': 'Test'}, ['bug'], 5
        )
        self.assertEqual(result['iid'], 10)


if __name__ == '__main__':
    unittest.main()
