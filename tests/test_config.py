import json
import os
import tempfile
import unittest

from config import load_settings


class ConfigTests(unittest.TestCase):
    def test_load_settings_reads_ini_and_templates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "config.ini")
            templates_path = os.path.join(temp_dir, "templates.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                handle.write(
                    "\n".join(
                        [
                            "[DEFAULT]",
                            "base_url=https://gitlab.example.com/",
                            "group_id=42",
                            "custom_template=Custom",
                            "GITLAB_TOKEN='secret'",
                            "squash_commits=true",
                            "delete_branch_after_merge=false",
                            "developer_email=dev@example.com",
                            "OPENAI_API_KEY=",
                            "incident_project_id=99",
                        ]
                    )
                )
            with open(templates_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "templates": [{"name": "Bug", "labels": ["Bug"]}],
                        "reviewers": [1, 2],
                        "productionMappings": {"99": {"stage": "deploy"}},
                    },
                    handle,
                )

            settings = load_settings(config_path, templates_path)

        self.assertEqual(settings.api_url, "https://gitlab.example.com/api/v4")
        self.assertEqual(settings.gitlab_token, "secret")
        self.assertFalse(settings.delete_branch)
        self.assertTrue(settings.squash_commits)
        self.assertEqual(settings.templates[0]["name"], "Bug")
        self.assertEqual(settings.reviewers, [1, 2])
        self.assertEqual(settings.production_mappings["99"]["stage"], "deploy")


if __name__ == "__main__":
    unittest.main()
