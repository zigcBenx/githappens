from __future__ import annotations

import datetime

from githappens.interactive import prompt_estimated_time, select_labels


def _create_issue(
    runtime,
    client,
    project_id,
    title: str,
    milestone_id,
    epic,
    iteration,
    settings: dict,
):
    issue_type = settings.get("type") or "issue"
    return client.create_issue(
        project_id,
        title,
        settings.get("labels"),
        milestone_id,
        epic,
        iteration,
        settings.get("weight"),
        settings.get("estimated_time"),
        issue_type=issue_type,
    )


def start_issue_creation(
    runtime,
    client,
    project_id,
    title: str,
    milestone_id,
    epic,
    iteration,
    selected_settings: dict,
    only_issue: bool,
):
    estimated_time = prompt_estimated_time()

    settings = dict(selected_settings or {})
    if estimated_time:
        settings["estimated_time"] = int(estimated_time)

    created_issue = _create_issue(
        runtime,
        client,
        project_id,
        title,
        milestone_id,
        epic,
        iteration,
        settings,
    )
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = client.create_branch(project_id, created_issue, runtime.main_branch)
    created_merge_request = client.create_merge_request(
        project_id,
        created_branch,
        created_issue,
        settings.get("labels"),
        milestone_id,
        runtime.main_branch,
        runtime.config.squash_commits,
        runtime.config.delete_branch_after_merge,
    )
    print(f"Merge request #{created_merge_request['iid']}: {created_merge_request['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(
        f"         git checkout -b '{created_merge_request['source_branch']}' "
        f"'origin/{created_merge_request['source_branch']}'"
    )
    print("to switch to new branch.")

    return created_issue


def _find_active_by_date(items: list[dict]) -> dict | None:
    today = datetime.date.today().strftime("%Y-%m-%d")
    active = [
        item
        for item in items
        if item["start_date"] and item["due_date"] and item["start_date"] <= today <= item["due_date"]
    ]
    active.sort(key=lambda item: item["due_date"])
    return active[0] if active else None


def get_current_milestone(client) -> dict:
    milestone = _find_active_by_date(client.list_milestones())
    if not milestone:
        raise ValueError("No active milestone found.")
    return milestone


def get_active_iteration(client) -> dict:
    iteration = _find_active_by_date(client.list_iterations())
    if not iteration:
        raise ValueError("No active iteration found.")
    return iteration


def process_report(runtime, client, text: str, minutes: int):
    incident_project_id = runtime.config.incident_project_id
    if not incident_project_id:
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    labels = sorted(label["name"] for label in client.list_group_labels("Department"))
    selected_label = select_labels(labels)

    incident_settings = {
        "labels": ["incident", "report"],
        "onlyIssue": True,
        "type": "incident",
    }
    if selected_label:
        incident_settings["labels"].append(selected_label)

    issue_title = f"Incident Report: {text}"
    created_issue = _create_issue(
        runtime,
        client,
        incident_project_id,
        issue_title,
        milestone_id=False,
        epic=False,
        iteration=get_active_iteration(client),
        settings=incident_settings,
    )

    print(f"Incident issue #{created_issue['iid']} created successfully.")
    print(f"Title: {issue_title}")

    try:
        client.close_issue(incident_project_id, created_issue["iid"])
    except Exception as exc:
        print(f"Error closing issue: {exc}")

    try:
        client.add_issue_spent_time(incident_project_id, created_issue["iid"], minutes)
        print(f"Added {minutes} minutes to issue time tracking.")
    except Exception as exc:
        print(f"Error adding time tracking: {exc}")
