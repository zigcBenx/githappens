from unittest.mock import patch, MagicMock

from templates import select_template


@patch("templates.inquirer.prompt")
@patch("templates.get_config")
def test_select_template(mock_get_config, mock_prompt):
    mock_config = MagicMock()
    mock_config.TEMPLATES = [{"name": "Template 1"}, {"name": "Template 2"}]
    mock_config.CUSTOM_TEMPLATE = "Custom"
    mock_get_config.return_value = mock_config

    mock_prompt.return_value = {"template": "Template 1"}

    result = select_template()
    assert result == "Template 1"


@patch("templates.inquirer.prompt")
@patch("templates.get_config")
def test_select_template_custom(mock_get_config, mock_prompt):
    mock_config = MagicMock()
    mock_config.TEMPLATES = [{"name": "Template 1"}]
    mock_config.CUSTOM_TEMPLATE = "Custom"
    mock_get_config.return_value = mock_config

    mock_prompt.return_value = {"template": "Custom"}

    result = select_template()
    assert result == "Custom"