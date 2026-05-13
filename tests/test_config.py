import json
import tempfile
import unittest
from pathlib import Path

from githappens.config import load_app_config
from githappens.templates import get_issue_settings, template_names


class ConfigTests(unittest.TestCase):
    def test_load_app_config_reads_ini_and_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            (root / "configs" / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.example.com",
                        "group_id=123",
                        "custom_template=Custom",
                        'GITLAB_TOKEN="token-value"',
                        "squash_commits=true",
                        "delete_branch_after_merge=false",
                        'developer_email="dev@example.com"',
                        "production_pipeline_name=deploy",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "configs" / "templates.json").write_text(
                json.dumps(
                    {
                        "templates": [{"name": "Bug", "labels": ["bug"]}],
                        "reviewers": [1, 2],
                        "productionMappings": {"42": {"stage": "deploy"}},
                    }
                ),
                encoding="utf-8",
            )

            config = load_app_config(root)

        self.assertEqual(config.api_url, "https://gitlab.example.com/api/v4")
        self.assertEqual(config.gitlab_token, "token-value")
        self.assertTrue(config.squash_commits)
        self.assertFalse(config.delete_branch_after_merge)
        self.assertEqual(config.developer_email, "dev@example.com")
        self.assertEqual(config.reviewers, [1, 2])
        self.assertEqual(config.production_mappings["42"]["stage"], "deploy")

    def test_template_helpers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            (root / "configs" / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.com",
                        "group_id=1",
                        "custom_template=Custom",
                        "GITLAB_TOKEN=token",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "configs" / "templates.json").write_text(
                json.dumps({"templates": [{"name": "Feature", "weight": 3}], "reviewers": []}),
                encoding="utf-8",
            )

            config = load_app_config(root)

        self.assertEqual(template_names(config), ["Feature", "Custom"])
        self.assertEqual(get_issue_settings(config, "Feature"), {"name": "Feature", "weight": 3})
        self.assertEqual(get_issue_settings(config, "Custom"), {})

    def test_load_app_config_reports_missing_templates_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            (root / "configs" / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.com",
                        "group_id=1",
                        "custom_template=Custom",
                        "GITLAB_TOKEN=token",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(FileNotFoundError, "Missing templates file"):
                load_app_config(root)

    def test_load_app_config_reports_invalid_templates_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "configs").mkdir()
            (root / "configs" / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.com",
                        "group_id=1",
                        "custom_template=Custom",
                        "GITLAB_TOKEN=token",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "configs" / "templates.json").write_text("{invalid", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Invalid templates file"):
                load_app_config(root)


if __name__ == "__main__":
    unittest.main()
