from typing import Any, Dict, List, Optional


def list_template_names(templates: List[Dict[str, Any]], custom_template: str) -> List[str]:
    template_names = [template["name"] for template in templates]
    template_names.append(custom_template)
    return template_names


def get_issue_settings(
    template_name: str,
    templates: List[Dict[str, Any]],
    custom_template: str,
) -> Optional[Dict[str, Any]]:
    if template_name == custom_template:
        return {}
    return next((template for template in templates if template["name"] == template_name), None)
