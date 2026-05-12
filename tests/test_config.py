import json
import tempfile
import unittest
from pathlib import Path

from config import load_app_config, load_template_config


class ConfigTests(unittest.TestCase):
    def test_load_app_config_reads_and_cleans_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.ini"
            config_path.write_text(
                "\n".join([
                    "[DEFAULT]",
                    "base_url=https://example.gitlab.com",
                    "group_id=42",
                    "custom_template=Custom template",
                    "GITLAB_TOKEN='secret'",
                    "delete_branch_after_merge=false",
                    "developer_email=\"dev@example.com\"",
                    "squash_commits=false",
                    "production_pipeline_name=deploy-prod",
                    "production_job_name=ship",
                    "production_ref=main",
                    "incident_project_id=123",
                    "OPENAI_API_KEY=key",
                ]),
                encoding="utf-8",
            )

            app_config = load_app_config(config_path)

        self.assertEqual(app_config.base_url, "https://example.gitlab.com")
        self.assertEqual(app_config.api_url, "https://example.gitlab.com/api/v4")
        self.assertEqual(app_config.group_id, "42")
        self.assertEqual(app_config.gitlab_token, "secret")
        self.assertFalse(app_config.delete_branch_after_merge)
        self.assertEqual(app_config.developer_email, "dev@example.com")

    def test_load_template_config_defaults_when_missing(self):
        template_config = load_template_config("/tmp/does-not-exist-githappens.json")

        self.assertEqual(template_config.templates, [])
        self.assertEqual(template_config.reviewers, [])
        self.assertEqual(template_config.production_mappings, {})

    def test_load_template_config_reads_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_path = Path(temp_dir) / "templates.json"
            templates_path.write_text(
                json.dumps({
                    "templates": [{"name": "Bug"}],
                    "reviewers": [1, 2],
                    "productionMappings": {"123": {"stage": "deploy"}},
                }),
                encoding="utf-8",
            )

            template_config = load_template_config(templates_path)

        self.assertEqual(template_config.templates, [{"name": "Bug"}])
        self.assertEqual(template_config.reviewers, [1, 2])
        self.assertEqual(template_config.production_mappings["123"]["stage"], "deploy")


if __name__ == "__main__":
    unittest.main()
