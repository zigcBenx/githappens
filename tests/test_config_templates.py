import json
import tempfile
import unittest

from githappens import config, templates


class ConfigTemplatesTest(unittest.TestCase):
    def test_load_config_reads_values(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as file:
            file.write("[DEFAULT]\nbase_url=https://gitlab.example.com\n")
            file_path = file.name

        parser = config.load_config(file_path)

        self.assertEqual(parser.get("DEFAULT", "base_url"), "https://gitlab.example.com")

    def test_load_template_config_reads_templates(self):
        payload = {"templates": [{"name": "Bug"}], "reviewers": [1]}
        with tempfile.NamedTemporaryFile("w", delete=False) as file:
            json.dump(payload, file)
            file_path = file.name

        self.assertEqual(templates.load_template_config(file_path), payload)

    def test_get_issue_settings_returns_matching_template(self):
        result = templates.get_issue_settings(
            "Bug",
            templates=[{"name": "Feature"}, {"name": "Bug", "labels": ["Bug"]}],
        )

        self.assertEqual(result, {"name": "Bug", "labels": ["Bug"]})

    def test_get_issue_settings_returns_empty_for_custom_template(self):
        self.assertEqual(templates.get_issue_settings(config.CUSTOM_TEMPLATE), {})

    def test_get_issue_settings_returns_empty_for_missing_template(self):
        result = templates.get_issue_settings("Missing", templates=[{"name": "Bug"}])

        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
