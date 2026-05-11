import unittest

from githappens.templates import get_issue_settings, normalize_labels


class TemplatesTest(unittest.TestCase):
    def test_custom_template_returns_empty_settings(self):
        templates = [{"name": "Bug", "labels": ["Bug"]}]

        self.assertEqual(get_issue_settings("Custom", templates, "Custom"), {})

    def test_named_template_returns_matching_settings(self):
        expected = {"name": "Bug", "labels": ["Bug"]}
        templates = [expected, {"name": "Feature", "labels": ["Feature"]}]

        self.assertEqual(get_issue_settings("Bug", templates, "Custom"), expected)

    def test_normalize_labels_joins_lists(self):
        self.assertEqual(normalize_labels(["Bug", "P::1"]), "Bug,P::1")


if __name__ == "__main__":
    unittest.main()
