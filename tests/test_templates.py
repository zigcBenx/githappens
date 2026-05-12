import unittest

from templates import get_issue_settings


class TemplateTests(unittest.TestCase):
    def test_get_issue_settings_returns_empty_for_custom_template(self):
        self.assertEqual(
            get_issue_settings("Custom", templates=[{"name": "Bug"}], custom_template="Custom"),
            {},
        )

    def test_get_issue_settings_finds_matching_template(self):
        templates = [
            {"name": "Bug", "labels": ["bug"]},
            {"name": "Feature", "labels": ["feature"]},
        ]

        self.assertEqual(
            get_issue_settings("Feature", templates=templates, custom_template="Custom"),
            {"name": "Feature", "labels": ["feature"]},
        )


if __name__ == "__main__":
    unittest.main()
