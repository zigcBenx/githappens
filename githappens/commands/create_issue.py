from __future__ import annotations

import datetime
import re
from typing import Any

from githappens import git_utils
from githappens.config import AppConfig
from githappens.gitlab_api import GitLabApi
from githappens.interactive import (
    select_epic,
    select_iteration,
    select_labels,
    select_milestone,
)


def resolve_project_id(api: GitLabApi) -> str | int:
    project_link = git_utils.get_project_link_from_current_dir()
    if not project_link:
        return enter_project_id()

    for project in api.get_all_projects(project_link):
        if project.get("ssh_url_to_repo") == project_link:
            return project["id"]
    return enter_project_id()


def enter_project_id() -> str:
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        print("Invalid project ID.")


def current_milestone(milestones: list[dict[str, Any]]) -> dict[str, Any] | None:
    today = datetime.date.today().strftime("%Y-%m-%d")
    active = [
        milestone
        for milestone in milestones
        if milestone.get("start_date") and milestone.get("due_date") and milestone["start_date"] <= today <= milestone["due_date"]
    ]
    active.sort(key=lambda milestone: milestone["due_date"])
    return active[0] if active else None


def get_selected_milestone(api: GitLabApi, manual: bool) -> dict[str, Any] | None:
    milestones = api.list_group_milestones()
    if manual:
        title = select_milestone(milestones)
        return next(milestone for milestone in milestones if milestone["title"] == title)
    return current_milestone(milestones)


def get_active_iteration(api: GitLabApi) -> dict[str, Any] | None:
    today = datetime.date.today().strftime("%Y-%m-%d")
    active = [
        iteration
        for iteration in api.list_group_iterations()
        if iteration.get("start_date") and iteration.get("due_date") and iteration["start_date"] <= today <= iteration["due_date"]
    ]
    active.sort(key=lambda iteration: iteration["due_date"])
    return active[0] if active else None


def get_selected_iteration(api: GitLabApi, manual: bool) -> dict[str, Any] | None:
    if not manual:
        return get_active_iteration(api)
    iterations = api.list_group_iterations()
    selected = select_iteration(iterations)
    return next(iteration for iteration in iterations if f"{iteration['start_date']} - {iteration['due_date']}" == selected)


def get_selected_epic(api: GitLabApi) -> dict[str, Any]:
    epics = api.list_group_epics()
    selected = select_epic(epics)
    return next(epic for epic in epics if epic["title"] == selected)


def create_issue(api: GitLabApi, project_id: str | int, title: str, milestone_id: Any, epic: Any, iteration: Any, settings: dict[str, Any]) -> dict[str, Any]:
    if not settings:
        print("No settings in template")
        raise SystemExit(2)
    issue_type = settings.get("type") or "issue"
    return api.create_issue(
        project_id,
        title,
        settings.get("labels"),
        milestone_id,
        epic,
        iteration,
        settings.get("weight"),
        settings.get("estimated_time"),
        issue_type,
    )


def slugify_branch_name(issue: dict[str, Any]) -> str:
    normalized_title = re.sub(r"[^a-z0-9]+", "-", issue["title"].lower()).strip("-")
    return f"{issue['iid']}-{normalized_title}"


def start_issue_creation(
    config: AppConfig,
    api: GitLabApi,
    project_id: str | int,
    title: str,
    milestone_id: Any,
    epic: Any,
    iteration: Any,
    selected_settings: dict[str, Any],
    only_issue: bool,
    main_branch: str,
    estimated_time: int | None = None,
) -> dict[str, Any]:
    if estimated_time:
        selected_settings = selected_settings.copy()
        selected_settings["estimated_time"] = estimated_time

    created_issue = create_issue(api, project_id, title, milestone_id, epic, iteration, selected_settings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    branch_name = slugify_branch_name(created_issue)
    created_branch = api.create_branch(project_id, branch_name, created_issue["iid"], main_branch)
    created_merge_request = api.create_merge_request(
        project_id,
        created_branch["name"],
        created_issue,
        selected_settings.get("labels"),
        milestone_id,
        main_branch,
    )
    print(f"Merge request #{created_merge_request['iid']}: {created_merge_request['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_merge_request['source_branch']}' 'origin/{created_merge_request['source_branch']}'")
    print("to switch to new branch.")
    return created_issue


def create_incident_report(config: AppConfig, api: GitLabApi, text: str, minutes: int) -> None:
    if not config.incident_project_id:
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    selected_label = select_labels(api, "Department")
    incident_settings: dict[str, Any] = {
        "labels": ["incident", "report"],
        "onlyIssue": True,
        "type": "incident",
    }
    if selected_label:
        incident_settings["labels"].append(selected_label)

    try:
        issue = create_issue(
            api,
            config.incident_project_id,
            f"Incident Report: {text}",
            False,
            False,
            get_active_iteration(api),
            incident_settings,
        )
        api.close_issue(config.incident_project_id, issue["iid"])
        print(f"Incident issue #{issue['iid']} created successfully.")
        print(f"Title: Incident Report: {text}")
        api.add_spent_time(config.incident_project_id, issue["iid"], minutes)
        print(f"Added {minutes} minutes to issue time tracking.")
    except Exception as error:
        print(f"Error creating incident issue: {error}")
