import inquirer

from config import CUSTOM_TEMPLATE, TEMPLATES


def select_template():
    template_names = [template["name"] for template in TEMPLATES]
    template_names.append(CUSTOM_TEMPLATE)
    questions = [
        inquirer.List(
            "template",
            message="Select template:",
            choices=template_names,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["template"]


def getIssueSettings(template_name):
    if template_name == CUSTOM_TEMPLATE:
        return {}
    return next((template for template in TEMPLATES if template["name"] == template_name), None)
