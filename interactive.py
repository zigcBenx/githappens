try:
    import inquirer
except ImportError:
    inquirer = None

from config import CUSTOM_TEMPLATE, REVIEWERS
from templates import template_names


def _inquirer():
    if inquirer is None:
        raise RuntimeError("The inquirer package is required for interactive prompts. Install it with: pip install inquirer")
    return inquirer


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        exit("Invalid project ID.")


def select_template():
    prompt = _inquirer()
    questions = [
        prompt.List(
            "template",
            message="Select template:",
            choices=template_names(custom_template=CUSTOM_TEMPLATE),
        ),
    ]
    answer = prompt.prompt(questions)
    return answer["template"]


def select_milestone(milestones):
    prompt = _inquirer()
    choices = [milestone["title"] for milestone in milestones]
    questions = [
        prompt.List(
            "milestones",
            message="Select milestone:",
            choices=choices,
        ),
    ]
    answer = prompt.prompt(questions)
    return answer["milestones"]


def select_iteration(iterations):
    prompt = _inquirer()
    choices = [f"{iteration['start_date']} - {iteration['due_date']}" for iteration in iterations]
    questions = [
        prompt.List(
            "iterations",
            message="Select iteration:",
            choices=choices,
        ),
    ]
    answer = prompt.prompt(questions)
    return answer["iterations"]


def select_epic(epics):
    prompt = _inquirer()
    choices = [epic["title"] for epic in epics]
    search_query = prompt.prompt([
        prompt.Text("search_query", message="Search epic:"),
    ])["search_query"]

    filtered_epics = [choice for choice in choices if search_query.lower() in choice.lower()]
    questions = [
        prompt.List(
            "epics",
            message="Select epic:",
            choices=filtered_epics,
        ),
    ]
    answer = prompt.prompt(questions)
    return answer["epics"]


def prompt_estimated_time():
    prompt = _inquirer()
    return prompt.prompt([
        prompt.Text(
            "estimated_time",
            message="Estimated time to complete this issue (in minutes, optional)",
            validate=lambda _, value: value == "" or value.isdigit(),
        )
    ])["estimated_time"]


def prompt_spent_time():
    prompt = _inquirer()
    return prompt.prompt([
        prompt.Text(
            "spent_time",
            message="How many minutes did you actually spend on this issue?",
            validate=lambda _, value: value.isdigit(),
        )
    ])["spent_time"]


def select_labels(labels, multiple=False):
    prompt = _inquirer()
    labels = sorted([label["name"] for label in labels])
    question_type = prompt.Checkbox if multiple else prompt.List
    questions = [
        question_type(
            "labels",
            message="Select one or more department labels:",
            choices=labels,
        ),
    ]
    answer = prompt.prompt(questions)
    return answer["labels"]


def choose_reviewers_manually(reviewers=None, get_user=None):
    prompt = _inquirer()
    reviewers = REVIEWERS if reviewers is None else reviewers
    reviewer_choices = []
    for reviewer_id in reviewers:
        if get_user is None:
            reviewer_choices.append((str(reviewer_id), reviewer_id))
            continue

        try:
            user = get_user(reviewer_id)
            if user:
                display_name = f"{user.get('name')} ({user.get('username')})"
                reviewer_choices.append((display_name, reviewer_id))
            else:
                reviewer_choices.append((str(reviewer_id), reviewer_id))
        except Exception:
            reviewer_choices.append((str(reviewer_id), reviewer_id))

    questions = [
        prompt.Checkbox(
            "selected_reviewers",
            message="Select reviewers",
            choices=[(name, str(reviewer_id)) for name, reviewer_id in reviewer_choices],
        )
    ]
    answers = prompt.prompt(questions)
    if answers and "selected_reviewers" in answers:
        return [int(reviewer_id) for reviewer_id in answers["selected_reviewers"]]
    return []
