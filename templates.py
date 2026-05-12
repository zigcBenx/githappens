from config import CUSTOM_TEMPLATE, TEMPLATES


def template_names(templates=None, custom_template=None):
    templates = TEMPLATES if templates is None else templates
    custom_template = CUSTOM_TEMPLATE if custom_template is None else custom_template
    names = [template["name"] for template in templates]
    names.append(custom_template)
    return names


def get_issue_settings(template_name, templates=None, custom_template=None):
    templates = TEMPLATES if templates is None else templates
    custom_template = CUSTOM_TEMPLATE if custom_template is None else custom_template
    if template_name == custom_template:
        return {}
    return next((template for template in templates if template["name"] == template_name), None)
