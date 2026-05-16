from __future__ import annotations

from typing import Any

from ..config import AppConfig
from ..gitlab_api import create_branch, create_issue, create_merge_request


def start_issue_creation(
    config: AppConfig,
    project_id: str | int,
    title: str,
    milestone: str | int | bool,
    epic: dict[str, Any] | bool,
    iteration: dict[str, Any] | bool,
    selected_settings: dict[str, Any],
    only_issue: bool,
) -> dict[str, Any]:
    import inquirer

    estimated_time = inquirer.prompt(
        [
            inquirer.Text(
                "estimated_time",
                message="Estimated time to complete this issue (in minutes, optional)",
                validate=lambda _, value: value == "" or value.isdigit(),
            )
        ]
    )["estimated_time"]

    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings["estimated_time"] = int(estimated_time_per_project)

    created_issue = create_issue(config, title, project_id, milestone, epic, iteration, selected_settings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = create_branch(config, project_id, created_issue)
    created_merge_request = create_merge_request(
        config,
        project_id,
        created_branch,
        created_issue,
        selected_settings.get("labels"),
        milestone,
    )
    print(f"Merge request #{created_merge_request['iid']}: {created_merge_request['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_merge_request['source_branch']}' 'origin/{created_merge_request['source_branch']}'")
    print("to switch to new branch.")
    return created_issue
