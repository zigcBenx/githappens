from unittest.mock import patch

import templates


def test_get_issue_settings_custom_template_returns_empty_dict():
    with patch("templates.config.CUSTOM_TEMPLATE", "CustomTmpl"):
        assert templates.getIssueSettings("CustomTmpl") == {}


def test_get_issue_settings_known_name_returns_template():
    fake_templates = [
        {"name": "Bug", "labels": ["bug"], "type": "issue"},
    ]
    with patch("templates.config.TEMPLATES", fake_templates):
        with patch("templates.config.CUSTOM_TEMPLATE", "Custom"):
            result = templates.getIssueSettings("Bug")
    assert result == fake_templates[0]
