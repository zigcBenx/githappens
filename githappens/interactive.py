from . import config
from . import templates as template_config


def get_inquirer():
    import inquirer

    return inquirer


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        exit("Invalid project ID.")


def select_template():
    inquirer = get_inquirer()
    template_names = [template["name"] for template in template_config.get_templates()]
    template_names.append(config.CUSTOM_TEMPLATE)
    answer = inquirer.prompt(
        [
            inquirer.List(
                "template",
                message="Select template:",
                choices=template_names,
            ),
        ]
    )
    return answer["template"]


def select_milestone(milestones):
    inquirer = get_inquirer()
    choices = [milestone["title"] for milestone in milestones]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "milestones",
                message="Select milestone:",
                choices=choices,
            ),
        ]
    )
    return answer["milestones"]


def select_iteration(iterations):
    inquirer = get_inquirer()
    choices = [
        iteration["start_date"] + " - " + iteration["due_date"]
        for iteration in iterations
    ]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "iterations",
                message="Select iteration:",
                choices=choices,
            ),
        ]
    )
    return answer["iterations"]


def select_epic(epics):
    inquirer = get_inquirer()
    names = [epic["title"] for epic in epics]
    search_query = inquirer.prompt(
        [inquirer.Text("search_query", message="Search epic:")]
    )["search_query"]
    filtered_epics = [choice for choice in names if search_query.lower() in choice.lower()]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "epics",
                message="Select epic:",
                choices=filtered_epics,
            ),
        ]
    )
    return answer["epics"]


def prompt_estimated_time():
    inquirer = get_inquirer()
    return inquirer.prompt(
        [
            inquirer.Text(
                "estimated_time",
                message="Estimated time to complete this issue (in minutes, optional)",
                validate=lambda _, value: value == "" or value.isdigit(),
            )
        ]
    )["estimated_time"]


def prompt_spent_time():
    inquirer = get_inquirer()
    return inquirer.prompt(
        [
            inquirer.Text(
                "spent_time",
                message="How many minutes did you actually spend on this issue?",
                validate=lambda _, value: value.isdigit(),
            )
        ]
    )["spent_time"]


def select_labels(labels, multiple=False):
    inquirer = get_inquirer()
    choices = sorted([label["name"] for label in labels])
    question_type = inquirer.Checkbox if multiple else inquirer.List
    answer = inquirer.prompt(
        [
            question_type(
                "labels",
                message="Select one or more department labels:",
                choices=choices,
            ),
        ]
    )
    return answer["labels"]


def choose_reviewers_manually(reviewers, fetch_user):
    inquirer = get_inquirer()
    reviewer_choices = []
    for reviewer_id in reviewers:
        try:
            user = fetch_user(reviewer_id)
            if user:
                display_name = f"{user.get('name')} ({user.get('username')})"
                reviewer_choices.append((display_name, reviewer_id))
            else:
                reviewer_choices.append((str(reviewer_id), reviewer_id))
        except Exception:
            reviewer_choices.append((str(reviewer_id), reviewer_id))

    answers = inquirer.prompt(
        [
            inquirer.Checkbox(
                "selected_reviewers",
                message="Select reviewers",
                choices=[(name, str(reviewer_id)) for name, reviewer_id in reviewer_choices],
            )
        ]
    )
    if answers and "selected_reviewers" in answers:
        return [int(reviewer) for reviewer in answers["selected_reviewers"]]
    return []
