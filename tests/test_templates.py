import unittest

import templates


class TemplateTests(unittest.TestCase):
    def test_get_issue_settings_returns_matching_template(self):
        settings = templates.get_issue_settings(
            "Bug",
            [{"name": "Bug", "labels": ["Bug"]}],
            "Custom",
        )

        self.assertEqual(settings["labels"], ["Bug"])

    def test_get_issue_settings_returns_empty_for_custom_template(self):
        self.assertEqual(templates.get_issue_settings("Custom", [], "Custom"), {})

    def test_list_template_names_appends_custom_template(self):
        names = templates.list_template_names([{"name": "Bug"}], "Custom")

        self.assertEqual(names, ["Bug", "Custom"])


if __name__ == "__main__":
    unittest.main()
