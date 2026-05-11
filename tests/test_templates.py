import unittest

from githappens.templates import get_issue_settings, get_template_names


class TemplateTests(unittest.TestCase):
    def test_get_template_names_appends_custom_template(self):
        templates = [{"name": "Bug"}, {"name": "Feature"}]
        self.assertEqual(
            get_template_names(templates, "Custom"),
            ["Bug", "Feature", "Custom"],
        )

    def test_get_issue_settings_returns_empty_dict_for_custom_template(self):
        templates = [{"name": "Bug", "labels": ["bug"]}]
        self.assertEqual(get_issue_settings("Custom", templates, "Custom"), {})

    def test_get_issue_settings_returns_matching_template(self):
        templates = [{"name": "Bug", "labels": ["bug"]}]
        self.assertEqual(
            get_issue_settings("Bug", templates, "Custom"),
            {"name": "Bug", "labels": ["bug"]},
        )
