import tempfile
import unittest
from pathlib import Path

from config import load_config, load_template_config


class ConfigTests(unittest.TestCase):
    def test_load_config_reads_values_and_strips_token_quotes(self):
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.ini"
            config_path.write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.example.com",
                        "group_id=42",
                        "custom_template=Other",
                        "GITLAB_TOKEN='secret'",
                        "delete_branch_after_merge=false",
                        "squash_commits=false",
                        "developer_email=dev@example.com",
                        "incident_project_id=99",
                    ]
                )
            )

            config = load_config(config_path)

            self.assertEqual(config.base_url, "https://gitlab.example.com")
            self.assertEqual(config.api_url, "https://gitlab.example.com/api/v4")
            self.assertEqual(config.group_id, "42")
            self.assertEqual(config.custom_template, "Other")
            self.assertEqual(config.gitlab_token, "secret")
            self.assertFalse(config.delete_branch_after_merge)
            self.assertFalse(config.squash_commits)
            self.assertEqual(config.developer_email, "dev@example.com")
            self.assertEqual(config.incident_project_id, "99")

    def test_load_template_config_returns_empty_defaults_when_file_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            result = load_template_config(Path(directory) / "missing.json")

        self.assertEqual(result["templates"], [])
        self.assertEqual(result["reviewers"], [])
        self.assertEqual(result["productionMappings"], {})


if __name__ == "__main__":
    unittest.main()
