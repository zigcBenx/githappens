import json
import tempfile
import unittest

import templates


class TemplatesTest(unittest.TestCase):
    def test_templates_loaded(self):
        """Verify templates module loads expected structures."""
        self.assertIsInstance(templates.TEMPLATES, list)
        self.assertIsInstance(templates.REVIEWERS, list)
        self.assertIsInstance(templates.PRODUCTION_MAPPINGS, dict)


if __name__ == "__main__":
    unittest.main()
