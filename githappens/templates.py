from __future__ import annotations

from typing import Any

from .config import AppConfig


def get_issue_settings(config: AppConfig, template_name: str) -> dict[str, Any]:
    if template_name == config.custom_template:
        return {}
    return next((t for t in config.templates if t["name"] == template_name), None)


def template_names(config: AppConfig) -> list[str]:
    names = [t["name"] for t in config.templates]
    names.append(config.custom_template)
    return names

