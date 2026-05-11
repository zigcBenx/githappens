import json
import os

import config


def load_template_config(path=config.TEMPLATES_PATH):
    if not os.path.exists(path):
        return {"templates": [], "reviewers": [], "productionMappings": {}}

    with open(path, "r", encoding="utf-8") as template_file:
        data = json.load(template_file)

    data.setdefault("templates", [])
    data.setdefault("reviewers", [])
    data.setdefault("productionMappings", {})
    return data


TEMPLATE_CONFIG = load_template_config()
TEMPLATES = TEMPLATE_CONFIG["templates"]
REVIEWERS = TEMPLATE_CONFIG["reviewers"]
PRODUCTION_MAPPINGS = TEMPLATE_CONFIG.get("productionMappings", {})


def get_issue_settings(template_name):
    if template_name == config.CUSTOM_TEMPLATE:
        return {}
    return next((template for template in TEMPLATES if template["name"] == template_name), None)
