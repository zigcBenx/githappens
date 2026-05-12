import json
import tempfile
import unittest
from pathlib import Path

from githappens.config import load_context


class LoadContextTest(unittest.TestCase):
    def test_loads_settings_templates_reviewers_and_mappings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            configs = root / "configs"
            configs.mkdir()
            (configs / "config.ini").write_text(
                "\n".join(
                    [
                        "[DEFAULT]",
                        "base_url=https://gitlab.example.test",
                        "group_id=123",
                        "custom_template=Custom",
                        "GITLAB_TOKEN='secret'",
                        "squash_commits=true",
                        "delete_branch_after_merge=false",
                        "developer_email=dev@example.test",
                    ]
                ),
                encoding="utf-8",
            )
            (configs / "templates.json").write_text(
                json.dumps(
                    {
                        "templates": [{"name": "Bug", "labels": ["bug"]}],
                        "reviewers": [1, 2],
                        "productionMappings": {"123": {"stage": "deploy"}},
                    }
                ),
                encoding="utf-8",
            )

            ctx = load_context(root)

        self.assertEqual(ctx.settings.base_url, "https://gitlab.example.test")
        self.assertEqual(ctx.settings.api_url, "https://gitlab.example.test/api/v4")
        self.assertEqual(ctx.settings.gitlab_token, "secret")
        self.assertFalse(ctx.settings.delete_branch_after_merge)
        self.assertEqual(ctx.templates[0]["name"], "Bug")
        self.assertEqual(ctx.reviewers, [1, 2])
        self.assertIn("123", ctx.production_mappings)


if __name__ == "__main__":
    unittest.main()
