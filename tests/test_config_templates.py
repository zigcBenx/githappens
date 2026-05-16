import json
import os
import tempfile
import unittest
from unittest.mock import patch

from githappens import config
from githappens.templates import get_issue_settings


class ConfigTemplateTests(unittest.TestCase):
    def tearDown(self):
        config.get_settings.cache_clear()
        config.get_template_config.cache_clear()

    def test_settings_reads_config_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.ini")
            with open(config_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "[DEFAULT]\n"
                    "base_url = https://gitlab.example.com\n"
                    "group_id = 42\n"
                    "custom_template = Custom\n"
                    "GITLAB_TOKEN = 'token-value'\n"
                    "delete_branch_after_merge = true\n"
                    "squash_commits = false\n"
                )

            with patch.object(config, "CONFIG_PATH", config_path):
                settings = config.get_settings()

        self.assertEqual(settings.api_url, "https://gitlab.example.com/api/v4")
        self.assertEqual(settings.gitlab_token, "token-value")
        self.assertTrue(settings.delete_branch)
        self.assertFalse(settings.squash_commits)

    def test_get_issue_settings_returns_template_by_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "templates.json")
            with open(template_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "templates": [{"name": "Bug", "labels": ["bug"]}],
                        "reviewers": [1],
                    },
                    handle,
                )

            with patch.object(config, "TEMPLATES_PATH", template_path), patch(
                "githappens.templates.get_settings"
            ) as get_settings:
                get_settings.return_value.custom_template = "Custom"
                settings = get_issue_settings("Bug")

        self.assertEqual(settings["labels"], ["bug"])


if __name__ == "__main__":
    unittest.main()
