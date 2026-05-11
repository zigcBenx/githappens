import unittest
from pathlib import Path

from githappens.config import AppConfig
from githappens.templates import get_issue_settings, template_names


def make_config():
    return AppConfig(
        root=Path("."),
        base_url="https://gitlab.example.com",
        api_url="https://gitlab.example.com/api/v4",
        group_id="1",
        custom_template="Custom",
        gitlab_token="token",
        delete_branch=True,
        developer_email=None,
        squash_commits=True,
        production_pipeline_name="deploy",
        production_job_name=None,
        production_ref=None,
        openai_api_key=None,
        incident_project_id=None,
        templates=[{"name": "Bug", "labels": ["bug"]}],
        reviewers=[],
        production_mappings={},
    )


class TemplatesTest(unittest.TestCase):
    def test_template_names_includes_custom_template_last(self):
        self.assertEqual(template_names(make_config()), ["Bug", "Custom"])

    def test_get_issue_settings_returns_empty_dict_for_custom_template(self):
        self.assertEqual(get_issue_settings(make_config(), "Custom"), {})

    def test_get_issue_settings_returns_named_template(self):
        self.assertEqual(get_issue_settings(make_config(), "Bug"), {"name": "Bug", "labels": ["bug"]})


if __name__ == "__main__":
    unittest.main()

