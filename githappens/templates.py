from __future__ import annotations

from typing import Any

from .config import AppConfig


def select_template(config: AppConfig) -> str:
    import inquirer

    template_names = [template["name"] for template in config.templates]
    template_names.append(config.custom_template)
    answer = inquirer.prompt(
        [
            inquirer.List(
                "template",
                message="Select template:",
                choices=template_names,
            )
        ]
    )
    return answer["template"]


def get_issue_settings(config: AppConfig, template_name: str) -> dict[str, Any]:
    if template_name == config.custom_template:
        return {}
    return next((template for template in config.templates if template["name"] == template_name), {})
