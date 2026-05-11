from __future__ import annotations


def get_template_names(templates: list[dict], custom_template: str) -> list[str]:
    names = [template["name"] for template in templates]
    names.append(custom_template)
    return names


def get_issue_settings(
    template_name: str, templates: list[dict], custom_template: str
) -> dict:
    if template_name == custom_template:
        return {}

    return next((template for template in templates if template["name"] == template_name), {})
