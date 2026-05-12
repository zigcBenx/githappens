import unittest
from types import SimpleNamespace

from githappens.templates import get_issue_settings


class TemplatesTest(unittest.TestCase):
    def test_custom_template_returns_empty_settings(self):
        ctx = SimpleNamespace(
            settings=SimpleNamespace(custom_template="Custom"),
            templates=[{"name": "Bug", "labels": ["bug"]}],
        )

        self.assertEqual(get_issue_settings(ctx, "Custom"), {})

    def test_named_template_returns_matching_settings(self):
        ctx = SimpleNamespace(
            settings=SimpleNamespace(custom_template="Custom"),
            templates=[{"name": "Bug", "labels": ["bug"]}],
        )

        self.assertEqual(get_issue_settings(ctx, "Bug"), {"name": "Bug", "labels": ["bug"]})


if __name__ == "__main__":
    unittest.main()
