def get_issue_settings(ctx, template_name):
    if template_name == ctx.settings.custom_template:
        return {}
    return next((template for template in ctx.templates if template["name"] == template_name), None)
