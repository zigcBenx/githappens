from __future__ import annotations


def _inquirer():
    import inquirer

    return inquirer


def select_template(template_names: list[str]) -> str:
    inquirer = _inquirer()
    questions = [
        inquirer.List(
            "template",
            message="Select template:",
            choices=template_names,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["template"]


def select_milestone(milestones: list[dict]) -> str:
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


def select_iteration(iterations: list[dict]) -> str:
    inquirer = _inquirer()
    choices = [f"{iteration['start_date']} - {iteration['due_date']}" for iteration in iterations]
    questions = [
        inquirer.List(
            "iterations",
            message="Select iteration:",
            choices=choices,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["iterations"]


def select_epic(epics: list[dict]) -> str:
    inquirer = _inquirer()
    search_query = inquirer.prompt(
        [inquirer.Text("search_query", message="Search epic:")]
    )["search_query"]
    filtered = [epic["title"] for epic in epics if search_query.lower() in epic["title"].lower()]
    questions = [
        inquirer.List(
            "epics",
            message="Select epic:",
            choices=filtered,
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


def select_labels(labels: list[str], multiple: bool = False):
    inquirer = _inquirer()
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


def choose_reviewers_manually(client, reviewer_ids: list[int]) -> list[int]:
    inquirer = _inquirer()
    reviewer_choices = []
    for reviewer_id in reviewer_ids:
        try:
            user = client.get_user(reviewer_id)
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
