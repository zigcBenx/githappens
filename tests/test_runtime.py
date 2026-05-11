import tempfile
import unittest
from pathlib import Path

from githappens.config import load_config
from githappens.runtime import load_runtime, load_templates


class RuntimeTests(unittest.TestCase):
    def test_load_config_coerces_boolean_and_optional_values(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            config_path.write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.example.com",
                        "group_id=42",
                        "custom_template=Custom",
                        'GITLAB_TOKEN="token-value"',
                        "squash_commits=false",
                        "delete_branch_after_merge=true",
                        'developer_email="dev@example.com"',
                        "OPENAI_API_KEY='sk-test'",
                        "incident_project_id='1234'",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_config(config_path)

        self.assertEqual(config.base_url, "https://gitlab.example.com")
        self.assertEqual(config.api_url, "https://gitlab.example.com/api/v4")
        self.assertEqual(config.group_id, "42")
        self.assertEqual(config.gitlab_token, "token-value")
        self.assertFalse(config.squash_commits)
        self.assertTrue(config.delete_branch_after_merge)
        self.assertEqual(config.developer_email, "dev@example.com")
        self.assertEqual(config.openai_api_key, "sk-test")
        self.assertEqual(config.incident_project_id, "1234")

    def test_load_templates_and_runtime(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.ini"
            templates_path = Path(tmpdir) / "templates.json"

            config_path.write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.example.com",
                        "group_id=99",
                        "custom_template=Custom",
                        "GITLAB_TOKEN=secret",
                        "squash_commits=true",
                        "delete_branch_after_merge=false",
                    ]
                ),
                encoding="utf-8",
            )
            templates_path.write_text(
                (
                    '{"templates":[{"name":"Bug","labels":["bug"]}],'
                    '"reviewers":[1,2],"productionMappings":{"99":{"stage":"deploy","job":"prod"}}}'
                ),
                encoding="utf-8",
            )

            templates, reviewers, production_mappings = load_templates(templates_path)
            runtime = load_runtime(config_path, templates_path)

        self.assertEqual(templates[0]["name"], "Bug")
        self.assertEqual(reviewers, [1, 2])
        self.assertEqual(production_mappings["99"]["job"], "prod")
        self.assertEqual(runtime.config.group_id, "99")
        self.assertEqual(runtime.reviewers, [1, 2])
        self.assertEqual(runtime.production_mappings["99"]["stage"], "deploy")
