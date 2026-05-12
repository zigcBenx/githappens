#!/usr/bin/env python3
import config
import gitlab_api
import interactive


def run(title, project_id, milestone, epic, iteration, selected_settings, only_issue):
    estimated_time = interactive.prompt_estimated_time()

    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings['estimated_time'] = int(estimated_time_per_project)

    issue_type = selected_settings.get('type') or 'issue'
    created_issue = gitlab_api.execute_issue_create(
        project_id,
        title,
        selected_settings.get('labels'),
        milestone,
        epic,
        iteration,
        selected_settings.get('weight'),
        selected_settings.get('estimated_time'),
        issue_type,
    )
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = gitlab_api.create_branch(project_id, created_issue)
    created_mr = gitlab_api.create_merge_request(
        project_id,
        created_branch,
        created_issue,
        selected_settings.get('labels'),
        milestone,
    )
    print(f"Merge request #{created_mr['iid']}: {created_mr['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_mr['source_branch']}' 'origin/{created_mr['source_branch']}'")
    print("to switch to new branch.")
    return created_issue
