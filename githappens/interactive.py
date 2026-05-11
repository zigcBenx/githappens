from __future__ import annotations

from typing import Any

from .config import AppConfig


def enter_project_id() -> str:
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        raise SystemExit("Invalid project ID.")


def select_milestone(milestones: list[dict[str, Any]]) -> str:
    import inquirer

    choices = [milestone["title"] for milestone in milestones]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "milestones",
                message="Select milestone:",
                choices=choices,
            )
        ]
    )
    return answer["milestones"]


def get_selected_milestone(milestone: str, milestones: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((item for item in milestones if item["title"] == milestone), None)


def select_iteration(iterations: list[dict[str, Any]]) -> str:
    import inquirer

    choices = [f"{iteration['start_date']} - {iteration['due_date']}" for iteration in iterations]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "iterations",
                message="Select iteration:",
                choices=choices,
            )
        ]
    )
    return answer["iterations"]


def get_selected_iteration(iteration: str, iterations: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((item for item in iterations if f"{item['start_date']} - {item['due_date']}" == iteration), None)


def select_epic(epics: list[dict[str, Any]]) -> str:
    import inquirer

    epic_titles = [epic["title"] for epic in epics]
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


def get_selected_epic(epic: str, epics: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((item for item in epics if item["title"] == epic), None)


def choose_reviewers_manually(config: AppConfig, get_user_details) -> list[int]:
    import inquirer

    reviewer_choices = []
    for reviewer_id in config.reviewers:
        user = get_user_details(reviewer_id)
        if user:
            display_name = f"{user.get('name')} ({user.get('username')})"
            reviewer_choices.append((display_name, reviewer_id))
        else:
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


def select_labels(labels: list[dict[str, Any]], multiple: bool = False) -> list[str] | str:
    import inquirer

    choices = sorted([label["name"] for label in labels])
    question_type = inquirer.Checkbox if multiple else inquirer.List
    answer = inquirer.prompt(
        [
            question_type(
                "labels",
                message="Select one or more department labels:",
                choices=choices,
            )
        ]
    )
    return answer["labels"]
