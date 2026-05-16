from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from githappens.config import load_app_config
from githappens.git_utils import branch_name_for_issue
from githappens.gitlab_api import build_issue_description, normalize_labels
from githappens.templates import get_issue_settings


class ConfigTests(unittest.TestCase):
    def test_load_app_config_reads_config_and_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            config_dir = root / "configs"
            config_dir.mkdir()
            (config_dir / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.example.com",
                        "group_id=123",
                        "custom_template=Custom",
                        "GITLAB_TOKEN='abc'",
                        "delete_branch_after_merge=true",
                        "squash_commits=false",
                    ]
                ),
                encoding="utf-8",
            )
            (config_dir / "templates.json").write_text(
                json.dumps(
                    {
                        "templates": [{"name": "Bug", "labels": ["bug"]}],
                        "reviewers": [1, 2],
                        "productionMappings": {"123": {"stage": "deploy", "job": "prod"}},
                    }
                ),
                encoding="utf-8",
            )

            config = load_app_config(root)

        self.assertEqual(config.base_url, "https://gitlab.example.com")
        self.assertEqual(config.api_url, "https://gitlab.example.com/api/v4")
        self.assertEqual(config.gitlab_token, "abc")
        self.assertFalse(config.squash_commits)
        self.assertEqual(config.templates[0]["name"], "Bug")
        self.assertEqual(config.production_mappings["123"]["job"], "prod")


class TemplateTests(unittest.TestCase):
    def test_get_issue_settings_returns_named_template_or_custom_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            config_dir = root / "configs"
            config_dir.mkdir()
            (config_dir / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.example.com",
                        "group_id=123",
                        "custom_template=Custom",
                        "GITLAB_TOKEN=abc",
                    ]
                ),
                encoding="utf-8",
            )
            (config_dir / "templates.json").write_text(
                json.dumps({"templates": [{"name": "Feature", "weight": 3}], "reviewers": []}),
                encoding="utf-8",
            )
            config = load_app_config(root)

        self.assertEqual(get_issue_settings(config, "Feature")["weight"], 3)
        self.assertEqual(get_issue_settings(config, "Custom"), {})


class HelperTests(unittest.TestCase):
    def test_branch_name_for_issue_matches_existing_slug_shape(self) -> None:
        branch_name = branch_name_for_issue({"iid": 42, "title": "Fix: Thing (Now)"})
        self.assertEqual(branch_name, "42-fix-thing--now")

    def test_normalize_labels_accepts_list_string_or_none(self) -> None:
        self.assertEqual(normalize_labels(["Bug", "P::1"]), "Bug,P::1")
        self.assertEqual(normalize_labels("Bug"), "Bug")
        self.assertIsNone(normalize_labels(None))

    def test_build_issue_description_preserves_iteration_and_estimate_commands(self) -> None:
        description = build_issue_description({"id": 7}, 30)
        self.assertIn("/iteration *iteration:7", description)
        self.assertIn("/estimate 30m", description)


if __name__ == "__main__":
    unittest.main()
