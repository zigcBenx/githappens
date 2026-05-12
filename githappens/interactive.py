import datetime

import inquirer
import requests

from . import config as settings
from . import gitlab_api


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        raise SystemExit("Invalid project ID.")


def get_selected_milestone(milestone, milestones):
    return next((item for item in milestones if item["title"] == milestone), None)


def select_milestone(milestones):
    answer = inquirer.prompt(
        [
            inquirer.List(
                "milestones",
                message="Select milestone:",
                choices=[item["title"] for item in milestones],
            )
        ]
    )
    return answer["milestones"]


def get_milestone(manual):
    milestones = gitlab_api.list_milestones()
    if manual:
        return get_selected_milestone(select_milestone(milestones), milestones)

    today = datetime.date.today().strftime("%Y-%m-%d")
    active_milestones = [
        milestone
        for milestone in milestones
        if milestone["start_date"] and milestone["due_date"] and milestone["start_date"] <= today <= milestone["due_date"]
    ]
    active_milestones.sort(key=lambda item: item["due_date"])
    return active_milestones[0]


def get_selected_iteration(iteration, iterations):
    return next((item for item in iterations if item["start_date"] + " - " + item["due_date"] == iteration), None)


def select_iteration(iterations):
    answer = inquirer.prompt(
        [
            inquirer.List(
                "iterations",
                message="Select iteration:",
                choices=[item["start_date"] + " - " + item["due_date"] for item in iterations],
            )
        ]
    )
    return answer["iterations"]


def get_active_iteration():
    iterations = gitlab_api.list_iterations()
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = [
        iteration
        for iteration in iterations
        if iteration["start_date"] and iteration["due_date"] and iteration["start_date"] <= today <= iteration["due_date"]
    ]
    active_iterations.sort(key=lambda item: item["due_date"])
    return active_iterations[0]


def get_iteration(manual):
    if manual:
        iterations = gitlab_api.list_iterations()
        return get_selected_iteration(select_iteration(iterations), iterations)
    return get_active_iteration()


def select_epic(epics):
    epic_titles = [item["title"] for item in epics]
    search_query = inquirer.prompt([inquirer.Text("search_query", message="Search epic:")])["search_query"]
    filtered_epics = [choice for choice in epic_titles if search_query.lower() in choice.lower()]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "epics",
                message="Select epic:",
                choices=filtered_epics,
            )
        ]
    )
    return answer["epics"]


def get_selected_epic(epic, epics):
    return next((item for item in epics if item["title"] == epic), None)


def get_epic():
    epics = gitlab_api.list_epics()
    return get_selected_epic(select_epic(epics), epics)


def choose_reviewers_manually():
    reviewer_choices = []
    for reviewer_id in settings.REVIEWERS:
        try:
            response = requests.get(
                f"{settings.API_URL}/users/{reviewer_id}",
                headers=gitlab_api.private_token_headers(),
            )
            if response.status_code == 200:
                user = response.json()
                reviewer_choices.append((f"{user.get('name')} ({user.get('username')})", reviewer_id))
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
        return [int(reviewer_id) for reviewer_id in answers["selected_reviewers"]]
    return []


def select_labels(search, multiple=False):
    labels = sorted(item["name"] for item in gitlab_api.get_labels_of_group(search))
    question_type = inquirer.Checkbox if multiple else inquirer.List
    answer = inquirer.prompt(
        [
            question_type(
                "labels",
                message="Select one or more department labels:",
                choices=labels,
            )
        ]
    )
    return answer["labels"]

