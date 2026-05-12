import unittest
from unittest.mock import patch
import templates

class TestTemplates(unittest.TestCase):
    @patch("templates.TEMPLATES", [{"name": "Bug", "type": "issue"}])
    @patch("templates.CUSTOM_TEMPLATE", "Custom")
    def test_get_issue_settings(self):
        # Test matching template
        settings = templates.get_issue_settings("Bug")
        self.assertEqual(settings['type'], 'issue')
        
        # Test custom template
        settings = templates.get_issue_settings("Custom")
        self.assertEqual(settings, {})
        
        # Test missing template
        settings = templates.get_issue_settings("Unknown")
        self.assertIsNone(settings)

if __name__ == '__main__':
    unittest.main()
