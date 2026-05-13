from __future__ import annotations

from typing import Any

from .config import AppConfig


def template_names(config: AppConfig) -> list[str]:
    names = [template["name"] for template in config.templates]
    names.append(config.custom_template)
    return names


def get_issue_settings(config: AppConfig, template_name: str) -> dict[str, Any]:
    if template_name == config.custom_template:
        return {}
    return next((template for template in config.templates if template["name"] == template_name), {})
