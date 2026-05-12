from config import CONFIG, TEMPLATES


def select_template(templates=None, custom_template=None):
    import inquirer

    templates = TEMPLATES if templates is None else templates
    custom_template = CONFIG.custom_template if custom_template is None else custom_template
    template_names = [template["name"] for template in templates]
    template_names.append(custom_template)
    questions = [
        inquirer.List(
            "template",
            message="Select template:",
            choices=template_names,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["template"]


def get_issue_settings(template_name, templates=None, custom_template=None):
    templates = TEMPLATES if templates is None else templates
    custom_template = CONFIG.custom_template if custom_template is None else custom_template
    if template_name == custom_template:
        return {}
    return next((template for template in templates if template["name"] == template_name), None)


# Backwards-compatible names.
getIssueSettings = get_issue_settings
