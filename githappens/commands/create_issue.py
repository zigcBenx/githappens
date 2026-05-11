from __future__ import annotations

from .. import git_utils, gitlab_api, interactive
from ..config import AppConfig


def create_issue(config: AppConfig, title, project_id, milestone_id, epic, iteration, settings):
    if not settings:
        print("No settings in template")
        raise SystemExit(2)
    issue_type = settings.get("type") or "issue"
    return gitlab_api.execute_issue_create(
        config,
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


def start_issue_creation(config: AppConfig, project_id, title, milestone, epic, iteration, selected_settings, only_issue):
    import inquirer

    estimated_time = inquirer.prompt(
        [
            inquirer.Text(
                "estimated_time",
                message="Estimated time to complete this issue (in minutes, optional)",
                validate=lambda _, x: x == "" or x.isdigit(),
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

    created_branch = gitlab_api.create_branch(config, project_id, created_issue)
    created_mr = gitlab_api.create_merge_request(
        config,
        project_id,
        created_branch,
        created_issue,
        selected_settings.get("labels"),
        milestone,
    )
    print(f"Merge request #{created_mr['iid']}: {created_mr['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_mr['source_branch']}' 'origin/{created_mr['source_branch']}'")
    print("to switch to new branch.")
    return created_issue


def run(config: AppConfig, args, title: str, selected_settings):
    if args.project_id and selected_settings.get("projectIds"):
        print("NOTE: Overwriting project id from argument...")

    project_id = selected_settings.get("projectIds") or args.project_id or interactive.get_project_id(config)
    milestone = False if args.no_milestone else interactive.get_milestone(config, args.milestone)["id"]
    iteration = False if args.no_iteration else interactive.get_iteration(config, True)
    epic = False if args.no_epic else interactive.get_epic(config)
    config.main_branch = git_utils.get_main_branch()
    only_issue = selected_settings.get("onlyIssue") or args.only_issue

    if isinstance(project_id, list):
        for id_ in project_id:
            start_issue_creation(config, id_, title, milestone, epic, iteration, selected_settings, only_issue)
    else:
        start_issue_creation(config, project_id, title, milestone, epic, iteration, selected_settings, only_issue)
