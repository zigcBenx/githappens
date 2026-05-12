import configparser

import gitlab_api
import interactive
from config import CONFIG_PARSER, INCIDENT_PROJECT_ID


def get_selected_milestone(milestone, milestones):
    return next((item for item in milestones if item["title"] == milestone), None)


def get_milestone(manual):
    if manual:
        milestones = gitlab_api.list_milestones()
        return get_selected_milestone(interactive.select_milestone(milestones), milestones)
    return gitlab_api.list_milestones(True)


def get_selected_iteration(iteration, iterations):
    return next((item for item in iterations if f"{item['start_date']} - {item['due_date']}" == iteration), None)


def get_iteration(manual):
    if manual:
        iterations = gitlab_api.list_iterations()
        return get_selected_iteration(interactive.select_iteration(iterations), iterations)
    return gitlab_api.get_active_iteration()


def get_selected_epic(epic, epics):
    return next((item for item in epics if item["title"] == epic), None)


def get_epic():
    epics = gitlab_api.list_epics()
    return get_selected_epic(interactive.select_epic(epics), epics)


def create_issue(title, project_id, milestone_id, epic, iteration, settings):
    if settings:
        issue_type = settings.get("type") or "issue"
        return gitlab_api.create_issue(
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
    exit(2)


def start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue, main_branch):
    estimated_time = interactive.prompt_estimated_time()

    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings["estimated_time"] = int(estimated_time_per_project)

    created_issue = create_issue(title, project_id, milestone, epic, iteration, selected_settings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = gitlab_api.create_branch(project_id, created_issue, main_branch)
    created_merge_request = gitlab_api.create_merge_request(
        project_id,
        created_branch,
        created_issue,
        selected_settings.get("labels"),
        milestone,
        main_branch,
    )
    print(f"Merge request #{created_merge_request['iid']}: {created_merge_request['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_merge_request['source_branch']}' 'origin/{created_merge_request['source_branch']}'")
    print("to switch to new branch.")

    return created_issue


def select_labels(search, multiple=False):
    labels = gitlab_api.get_labels_of_group(search)
    return interactive.select_labels(labels, multiple)


def process_report(text, minutes):
    try:
        incident_project_id = INCIDENT_PROJECT_ID or CONFIG_PARSER.get("DEFAULT", "incident_project_id")
    except (configparser.NoOptionError, configparser.NoSectionError):
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"
    selected_label = select_labels("Department")

    incident_settings = {
        "labels": ["incident", "report"],
        "onlyIssue": True,
        "type": "incident",
    }

    if selected_label:
        incident_settings["labels"].append(selected_label)

    try:
        iteration = gitlab_api.get_active_iteration()
        created_issue = create_issue(issue_title, incident_project_id, False, False, iteration, incident_settings)
        issue_iid = created_issue["iid"]

        gitlab_api.close_issue(issue_iid, incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        try:
            gitlab_api.add_spent_time(issue_iid, incident_project_id, minutes)
            print(f"Added {minutes} minutes to issue time tracking.")
        except Exception as e:
            print(f"Error adding time tracking: {str(e)}")

    except Exception as e:
        print(f"Error creating incident issue: {str(e)}")
