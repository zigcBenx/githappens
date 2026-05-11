import unittest

import config


class ConfigTests(unittest.TestCase):
    def test_paths_are_repo_relative(self):
        self.assertTrue(config.CONFIG_PATH.endswith("configs\\config.ini") or config.CONFIG_PATH.endswith("configs/config.ini"))
        self.assertTrue(config.TEMPLATES_PATH.endswith("configs\\templates.json") or config.TEMPLATES_PATH.endswith("configs/templates.json"))

    def test_boolean_parser_accepts_true_string(self):
        self.assertTrue(config._get_bool("missing-test-key", True))
        self.assertFalse(config._get_bool("missing-test-key", False))


if __name__ == "__main__":
    unittest.main()
