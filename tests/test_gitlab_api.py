import unittest
from unittest.mock import patch, MagicMock
import gitlab_api

class TestGitlabApi(unittest.TestCase):
    @patch("requests.get")
    def test_get_all_projects(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 123, "ssh_url_to_repo": "git@gitlab.com:test/proj.git"}]
        mock_get.return_value = mock_response
        
        res = gitlab_api.get_all_projects("git@gitlab.com:test/proj.git")
        self.assertEqual(res[0]["id"], 123)

if __name__ == '__main__':
    unittest.main()
