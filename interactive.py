from typing import Iterable, List

import templates as template_config


def _inquirer():
    import inquirer

    return inquirer


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        raise SystemExit("Invalid project ID.")


def select_template(templates, custom_template):
    inquirer = _inquirer()
    questions = [
        inquirer.List(
            "template",
            message="Select template:",
            choices=template_config.list_template_names(templates, custom_template),
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["template"]


def select_milestone(milestones):
    inquirer = _inquirer()
    questions = [
        inquirer.List(
            "milestones",
            message="Select milestone:",
            choices=[milestone["title"] for milestone in milestones],
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["milestones"]


def select_iteration(iterations):
    inquirer = _inquirer()
    choices = [iteration["start_date"] + " - " + iteration["due_date"] for iteration in iterations]
    questions = [
        inquirer.List(
            "iterations",
            message="Select iteration:",
            choices=choices,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["iterations"]


def select_epic(epics):
    inquirer = _inquirer()
    epic_titles = [epic["title"] for epic in epics]
    search_query = inquirer.prompt(
        [inquirer.Text("search_query", message="Search epic:")]
    )["search_query"]

    filtered_epics = [choice for choice in epic_titles if search_query.lower() in choice.lower()]
    questions = [
        inquirer.List(
            "epics",
            message="Select epic:",
            choices=filtered_epics,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["epics"]


def prompt_estimated_time() -> str:
    inquirer = _inquirer()
    return inquirer.prompt(
        [
            inquirer.Text(
                "estimated_time",
                message="Estimated time to complete this issue (in minutes, optional)",
                validate=lambda _, value: value == "" or value.isdigit(),
            )
        ]
    )["estimated_time"]


def select_labels(labels, multiple: bool = False):
    inquirer = _inquirer()
    labels = sorted([label["name"] for label in labels])
    question_type = inquirer.Checkbox if multiple else inquirer.List
    questions = [
        question_type(
            "labels",
            message="Select one or more department labels:",
            choices=labels,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["labels"]


def prompt_spent_time() -> str:
    inquirer = _inquirer()
    return inquirer.prompt(
        [
            inquirer.Text(
                "spent_time",
                message="How many minutes did you actually spend on this issue?",
                validate=lambda _, value: value.isdigit(),
            )
        ]
    )["spent_time"]


def choose_reviewers_manually(api, reviewer_ids: Iterable[int]) -> List[int]:
    inquirer = _inquirer()
    reviewer_choices = []
    for reviewer_id in reviewer_ids:
        try:
            user = api.get_user(reviewer_id)
            display_name = f"{user.get('name')} ({user.get('username')})"
            reviewer_choices.append((display_name, reviewer_id))
        except Exception:
            reviewer_choices.append((str(reviewer_id), reviewer_id))

    questions = [
        inquirer.Checkbox(
            "selected_reviewers",
            message="Select reviewers",
            choices=[(name, str(reviewer_id)) for name, reviewer_id in reviewer_choices],
        )
    ]
    answers = inquirer.prompt(questions)
    if answers and "selected_reviewers" in answers:
        return [int(reviewer_id) for reviewer_id in answers["selected_reviewers"]]
    return []
