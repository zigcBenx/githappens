import json

from . import config


def load_template_config(path=config.TEMPLATES_PATH):
    with open(path, "r") as file:
        return json.load(file)


def get_template_data():
    return load_template_config()


def get_templates():
    return get_template_data()["templates"]


def get_reviewers():
    return get_template_data()["reviewers"]


def get_production_mappings():
    return get_template_data().get("productionMappings", {})


def get_issue_settings(template_name, templates=None):
    if template_name == config.CUSTOM_TEMPLATE:
        return {}
    templates = templates if templates is not None else get_templates()
    return next((template for template in templates if template["name"] == template_name), {})
