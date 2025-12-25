import inquirer

from config import get_config


def select_template():
    config = get_config()
    template_names = [t['name'] for t in config.TEMPLATES]
    template_names.append(config.CUSTOM_TEMPLATE)
    questions = [
        inquirer.List('template',
                      message="Select template:",
                      choices=template_names,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['template']
