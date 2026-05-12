import templates


def test_get_issue_settings_returns_empty_for_custom(monkeypatch):
    monkeypatch.setattr(templates, "CUSTOM_TEMPLATE", "Custom")

    assert templates.getIssueSettings("Custom") == {}


def test_get_issue_settings_finds_named_template(monkeypatch):
    expected = {"name": "Bug", "labels": ["Bug"]}
    monkeypatch.setattr(templates, "CUSTOM_TEMPLATE", "Custom")
    monkeypatch.setattr(templates, "TEMPLATES", [expected])

    assert templates.getIssueSettings("Bug") == expected
