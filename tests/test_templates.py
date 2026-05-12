import unittest

from templates import get_issue_settings, template_names


class TemplateTests(unittest.TestCase):
    def test_template_names_appends_custom_template(self):
        names = template_names([{"name": "Bug"}, {"name": "Feature"}], "Custom")

        self.assertEqual(names, ["Bug", "Feature", "Custom"])

    def test_get_issue_settings_returns_template_or_custom_settings(self):
        templates = [{"name": "Bug", "labels": ["Bug"]}]

        self.assertEqual(get_issue_settings("Bug", templates, "Custom"), templates[0])
        self.assertEqual(get_issue_settings("Custom", templates, "Custom"), {})
        self.assertIsNone(get_issue_settings("Missing", templates, "Custom"))


if __name__ == "__main__":
    unittest.main()
