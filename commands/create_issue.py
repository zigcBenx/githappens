import subprocess
from typing import Any, Dict

import git_utils
import interactive


def resolve_project_id(api):
    project_link = git_utils.get_project_link_from_current_dir()
    if project_link == -1:
        return interactive.enter_project_id()

    all_projects = api.get_all_projects(project_link)
    matching_id = None
    for project in all_projects or []:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def get_selected_milestone(milestone, milestones):
    return next((item for item in milestones if item["title"] == milestone), None)


def get_milestone(api, manual):
    if manual:
        milestones = api.list_milestones()
        return get_selected_milestone(interactive.select_milestone(milestones), milestones)
    return api.list_milestones(True)


def get_selected_iteration(iteration, iterations):
    return next(
        (item for item in iterations if item["start_date"] + " - " + item["due_date"] == iteration),
        None,
    )


def get_iteration(api, manual):
    if manual:
        iterations = api.list_iterations()
        return get_selected_iteration(interactive.select_iteration(iterations), iterations)
    return api.get_active_iteration()


def get_selected_epic(epic, epics):
    return next((item for item in epics if item["title"] == epic), None)


def get_epic(api):
    epics = api.list_epics()
    return get_selected_epic(interactive.select_epic(epics), epics)


def create_issue(api, title, project_id, milestone_id, epic, iteration, settings):
    if settings:
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

    print("No settings in template")
    raise SystemExit(2)


def start_issue_creation(
    api,
    title: str,
    project_id,
    milestone_id,
    epic,
    iteration,
    selected_settings: Dict[str, Any],
    only_issue: bool,
    main_branch: str,
):
    estimated_time = interactive.prompt_estimated_time()

    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings["estimated_time"] = int(estimated_time_per_project)

    created_issue = create_issue(
        api,
        title,
        project_id,
        milestone_id,
        epic,
        iteration,
        selected_settings,
    )
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = api.create_branch(project_id, created_issue, main_branch)
    created_mr = api.create_merge_request(
        project_id,
        created_branch,
        created_issue,
        selected_settings.get("labels"),
        milestone_id,
        main_branch,
    )
    print(f"Merge request #{created_mr['iid']}: {created_mr['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_mr['source_branch']}' 'origin/{created_mr['source_branch']}'")
    print("to switch to new branch.")

    return created_issue


def process_report(api, settings, text: str, minutes: int):
    if not settings.incident_project_id:
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"
    selected_label = interactive.select_labels(api.get_labels_of_group("Department"))
    incident_settings = {
        "labels": ["incident", "report"],
        "onlyIssue": True,
        "type": "incident",
    }

    if selected_label:
        incident_settings["labels"].append(selected_label)

    try:
        iteration = api.get_active_iteration()
        created_issue = create_issue(
            api,
            issue_title,
            settings.incident_project_id,
            False,
            False,
            iteration,
            incident_settings,
        )
        issue_iid = created_issue["iid"]

        api.close_opened_issue(issue_iid, settings.incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        try:
            api.add_spent_time(settings.incident_project_id, issue_iid, minutes)
            print(f"Added {minutes} minutes to issue time tracking.")
        except subprocess.CalledProcessError as error:
            print(f"Error adding time tracking: {str(error)}")

    except Exception as error:
        print(f"Error creating incident issue: {str(error)}")
