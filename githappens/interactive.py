from __future__ import annotations

from typing import Any

from .config import AppConfig
from .gitlab_api import GitLabApi
from .templates import template_names


def _inquirer():
    import inquirer

    return inquirer


def select_template(config: AppConfig) -> str:
    inquirer = _inquirer()
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


def select_milestone(milestones: list[dict[str, Any]]) -> str:
    inquirer = _inquirer()
    answer = inquirer.prompt(
        [
            inquirer.List(
                "milestones",
                message="Select milestone:",
                choices=[milestone["title"] for milestone in milestones],
            ),
        ]
    )
    return answer["milestones"]


def select_iteration(iterations: list[dict[str, Any]]) -> str:
    inquirer = _inquirer()
    choices = [f"{iteration['start_date']} - {iteration['due_date']}" for iteration in iterations]
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


def select_epic(epics: list[dict[str, Any]]) -> str:
    inquirer = _inquirer()
    titles = [epic["title"] for epic in epics]
    search_query = inquirer.prompt([inquirer.Text("search_query", message="Search epic:")])["search_query"]
    choices = [title for title in titles if search_query.lower() in title.lower()]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "epics",
                message="Select epic:",
                choices=choices,
            ),
        ]
    )
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


def choose_reviewers_manually(config: AppConfig, api: GitLabApi) -> list[int]:
    inquirer = _inquirer()
    choices: list[tuple[str, str]] = []
    for reviewer_id in config.reviewers:
        user = api.get_user(reviewer_id)
        if user:
            choices.append((f"{user.get('name')} ({user.get('username')})", str(reviewer_id)))
        else:
            choices.append((str(reviewer_id), str(reviewer_id)))

    answers = inquirer.prompt(
        [
            inquirer.Checkbox(
                "selected_reviewers",
                message="Select reviewers",
                choices=choices,
            )
        ]
    )
    if answers and "selected_reviewers" in answers:
        return [int(reviewer) for reviewer in answers["selected_reviewers"]]
    return []


def select_labels(api: GitLabApi, search: str, multiple: bool = False) -> str | list[str]:
    inquirer = _inquirer()
    labels = sorted(label["name"] for label in api.list_group_labels(search))
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
