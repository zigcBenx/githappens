import inquirer

from . import config as settings


def select_template():
    template_names = [template["name"] for template in settings.TEMPLATES]
    template_names.append(settings.CUSTOM_TEMPLATE)
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


def get_issue_settings(template_name):
    if template_name == settings.CUSTOM_TEMPLATE:
        return {}
    return next((template for template in settings.TEMPLATES if template["name"] == template_name), None)

