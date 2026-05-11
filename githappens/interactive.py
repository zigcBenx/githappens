from __future__ import annotations

import datetime

from . import git_utils, gitlab_api
from .config import AppConfig
from .templates import template_names


def get_project_id(config: AppConfig):
    project_link = git_utils.get_project_link_from_current_dir()
    if project_link == -1:
        return enter_project_id()

    all_projects = gitlab_api.get_all_projects(config, project_link)
    for project in all_projects or []:
        if project.get("ssh_url_to_repo") == project_link:
            return project.get("id")
    return None


def enter_project_id() -> str:
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        raise SystemExit("Invalid project ID.")


def select_template(config: AppConfig) -> str:
    import inquirer

    answer = inquirer.prompt(
        [
            inquirer.List(
                "template",
                message="Select template:",
                choices=template_names(config),
            ),
        ]
    )
    return answer["template"]


def get_milestone(config: AppConfig, manual: bool):
    milestones = gitlab_api.list_milestones(config)
    if manual:
        return get_selected_milestone(select_milestone(milestones), milestones)
    today = datetime.date.today().strftime("%Y-%m-%d")
    active = [
        milestone
        for milestone in milestones
        if milestone["start_date"] and milestone["due_date"] and milestone["start_date"] <= today <= milestone["due_date"]
    ]
    active.sort(key=lambda x: x["due_date"])
    return active[0]


def select_milestone(milestones) -> str:
    import inquirer

    answer = inquirer.prompt(
        [
            inquirer.List(
                "milestones",
                message="Select milestone:",
                choices=[t["title"] for t in milestones],
            ),
        ]
    )
    return answer["milestones"]


def get_selected_milestone(milestone, milestones):
    return next((t for t in milestones if t["title"] == milestone), None)


def get_iteration(config: AppConfig, manual: bool):
    if manual:
        iterations = gitlab_api.list_iterations(config)
        return get_selected_iteration(select_iteration(iterations), iterations)
    return get_active_iteration(config)


def select_iteration(iterations) -> str:
    import inquirer

    choices = [t["start_date"] + " - " + t["due_date"] for t in iterations]
    answer = inquirer.prompt([inquirer.List("iterations", message="Select iteration:", choices=choices)])
    return answer["iterations"]


def get_selected_iteration(iteration, iterations):
    return next((t for t in iterations if t["start_date"] + " - " + t["due_date"] == iteration), None)


def get_active_iteration(config: AppConfig):
    today = datetime.date.today().strftime("%Y-%m-%d")
    active = [
        iteration
        for iteration in gitlab_api.list_iterations(config)
        if iteration["start_date"] and iteration["due_date"] and iteration["start_date"] <= today <= iteration["due_date"]
    ]
    active.sort(key=lambda x: x["due_date"])
    return active[0]


def get_epic(config: AppConfig):
    epics = gitlab_api.list_epics(config)
    return get_selected_epic(select_epic(epics), epics)


def select_epic(epics) -> str:
    import inquirer

    names = [t["title"] for t in epics]
    search_query = inquirer.prompt([inquirer.Text("search_query", message="Search epic:")])["search_query"]
    filtered_epics = [choice for choice in names if search_query.lower() in choice.lower()]
    answer = inquirer.prompt([inquirer.List("epics", message="Select epic:", choices=filtered_epics)])
    return answer["epics"]


def get_selected_epic(epic, epics):
    return next((t for t in epics if t["title"] == epic), None)


def select_labels(config: AppConfig, search: str, multiple: bool = False):
    import inquirer

    labels = sorted([t["name"] for t in gitlab_api.list_group_labels(config, search)])
    question_type = inquirer.Checkbox if multiple else inquirer.List
    answer = inquirer.prompt(
        [
            question_type(
                "labels",
                message="Select one or more department labels:",
                choices=labels,
            ),
        ]
    )
    return answer["labels"]


def choose_reviewers_manually(config: AppConfig):
    import inquirer
    import requests

    reviewer_choices = []
    for reviewer_id in config.reviewers:
        try:
            response = requests.get(f"{config.api_url}/users/{reviewer_id}", headers=gitlab_api.headers(config))
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
                choices=[(name, str(rid)) for name, rid in reviewer_choices],
            )
        ]
    )
    if answers and "selected_reviewers" in answers:
        return [int(r) for r in answers["selected_reviewers"]]
    return []
