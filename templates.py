from config import TEMPLATES, CUSTOM_TEMPLATE

def get_issue_settings(template_name):
    if template_name == CUSTOM_TEMPLATE:
        return {}
    return next((t for t in TEMPLATES if t['name'] == template_name), None)
