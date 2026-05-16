from .config import get_settings, get_templates


def select_template(prompt_list):
    settings = get_settings()
    template_names = [template["name"] for template in get_templates()]
    template_names.append(settings.custom_template)
    answer = prompt_list(
        "template",
        message="Select template:",
        choices=template_names,
    )
    return answer["template"]


def get_issue_settings(template_name):
    settings = get_settings()
    if template_name == settings.custom_template:
        return {}
    return next((template for template in get_templates() if template["name"] == template_name), None)
