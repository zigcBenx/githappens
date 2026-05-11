"""Template processing helpers."""

from __future__ import annotations

from typing import Any


def template_names(templates: list[dict[str, Any]], custom_template: str) -> list[str]:
    """Return interactive template names including the custom option."""
    return [template["name"] for template in templates] + [custom_template]


def get_issue_settings(
    template_name: str,
    templates: list[dict[str, Any]],
    custom_template: str,
) -> dict[str, Any]:
    """Return settings for a selected issue template.

    Custom templates intentionally return an empty dict to preserve the legacy
    behavior where custom selection is acknowledged but not yet implemented.
    """
    if template_name == custom_template:
        return {}
    return next((template for template in templates if template["name"] == template_name), {})


def normalize_labels(labels: str | list[str] | None) -> str | None:
    """Convert labels into GitLab's comma-separated API format."""
    if isinstance(labels, list):
        return ",".join(labels)
    return labels
