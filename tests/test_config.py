import unittest
from unittest.mock import patch, mock_open
import config

class TestConfig(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data='{"templates": [], "reviewers": []}')
    @patch("configparser.ConfigParser.read")
    def test_config_loading(self, mock_read, mock_file):
        # This is a basic smoke test to ensure config can be imported
        self.assertTrue(hasattr(config, 'API_URL'))
        self.assertTrue(hasattr(config, 'GITLAB_TOKEN'))

if __name__ == '__main__':
    unittest.main()
