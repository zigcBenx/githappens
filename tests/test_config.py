import json
import tempfile
import unittest
from pathlib import Path

from githappens.config import load_config


class LoadConfigTest(unittest.TestCase):
    def test_loads_config_and_templates_from_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "configs"
            config_dir.mkdir()
            (config_dir / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.example.com",
                        "group_id=42",
                        "custom_template=Custom",
                        "GITLAB_TOKEN='token'",
                        "squash_commits=true",
                        "delete_branch_after_merge=false",
                    ]
                ),
                encoding="utf-8",
            )
            (config_dir / "templates.json").write_text(
                json.dumps(
                    {
                        "templates": [{"name": "Bug", "labels": ["bug"]}],
                        "reviewers": [1, 2],
                        "productionMappings": {"42": {"stage": "deploy", "job": "prod"}},
                    }
                ),
                encoding="utf-8",
            )

            config = load_config(root)

        self.assertEqual(config.api_url, "https://gitlab.example.com/api/v4")
        self.assertEqual(config.group_id, "42")
        self.assertEqual(config.gitlab_token, "token")
        self.assertFalse(config.delete_branch)
        self.assertTrue(config.squash_commits)
        self.assertEqual(config.templates[0]["name"], "Bug")
        self.assertEqual(config.reviewers, [1, 2])
        self.assertEqual(config.production_mappings["42"]["job"], "prod")


if __name__ == "__main__":
    unittest.main()

