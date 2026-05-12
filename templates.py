#!/usr/bin/env python3
import inquirer

import config


def select_template():
    template_names = [t['name'] for t in config.TEMPLATES]
    template_names.append(config.CUSTOM_TEMPLATE)
    questions = [
        inquirer.List('template',
                      message="Select template:",
                      choices=template_names),
    ]
    answer = inquirer.prompt(questions)
    return answer['template']


def get_issue_settings(template_name):
    if template_name == config.CUSTOM_TEMPLATE:
        return {}
    return next((t for t in config.TEMPLATES if t['name'] == template_name), None)
