import configparser
import tempfile
import unittest

import config


class ConfigTest(unittest.TestCase):
    def test_config_values_loaded(self):
        """Verify that config module loads expected keys."""
        self.assertIsNotNone(config.BASE_URL)
        self.assertIsNotNone(config.API_URL)
        self.assertIsNotNone(config.GROUP_ID)
        self.assertIsNotNone(config.GITLAB_TOKEN)

    def test_custom_config_path(self):
        """Verify loading from a custom config file."""
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".ini") as f:
            f.write("[DEFAULT]\nbase_url=https://gitlab.test.com\ngroup_id=42\n")
            path = f.name

        cfg = configparser.ConfigParser()
        cfg.read(path)
        self.assertEqual(cfg.get("DEFAULT", "base_url"), "https://gitlab.test.com")
        self.assertEqual(cfg.get("DEFAULT", "group_id"), "42")


if __name__ == "__main__":
    unittest.main()
