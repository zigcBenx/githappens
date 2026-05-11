import json
import os
import tempfile
import unittest

import templates


class TemplateTests(unittest.TestCase):
    def test_load_template_config_adds_missing_optional_keys(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "templates.json")
            with open(template_path, "w", encoding="utf-8") as handle:
                json.dump({"templates": [{"name": "Bug"}]}, handle)

            result = templates.load_template_config(template_path)

        self.assertEqual(result["templates"][0]["name"], "Bug")
        self.assertEqual(result["reviewers"], [])
        self.assertEqual(result["productionMappings"], {})

    def test_missing_template_config_is_empty(self):
        result = templates.load_template_config("does-not-exist.json")
        self.assertEqual(result, {"templates": [], "reviewers": [], "productionMappings": {}})


if __name__ == "__main__":
    unittest.main()
