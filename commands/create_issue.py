import inquirer

from git_utils import getProjectLinkFromCurrentDir
from gitlab_api import (
    closeOpenedIssue,
    create_branch,
    create_merge_request,
    executeIssueCreate,
    getActiveIteration,
    get_all_projects,
    list_epics,
    list_iterations,
    list_milestones,
)
from interactive import (
    enterProjectId,
    getSelectedEpic,
    getSelectedIteration,
    getSelectedMilestone,
    select_epic,
    select_iteration,
    select_milestone,
    selectLabels,
)


def get_project_id():
    project_link = getProjectLinkFromCurrentDir()
    if project_link == -1:
        return enterProjectId()

    all_projects = get_all_projects(project_link)
    matching_id = None
    for project in all_projects:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def get_milestone(manual):
    if manual:
        milestones = list_milestones()
        return getSelectedMilestone(select_milestone(milestones), milestones)
    return list_milestones(True)


def get_iteration(manual):
    if manual:
        iterations = list_iterations()
        return getSelectedIteration(select_iteration(iterations), iterations)
    return getActiveIteration()


def get_epic():
    epics = list_epics()
    return getSelectedEpic(select_epic(epics), epics)


def createIssue(title, project_id, milestoneId, epic, iteration, settings):
    if settings:
        issue_type = settings.get("type") or "issue"
        return executeIssueCreate(
            project_id,
            title,
            settings.get("labels"),
            milestoneId,
            epic,
            iteration,
            settings.get("weight"),
            settings.get("estimated_time"),
            issue_type,
        )
    print("No settings in template")
    exit(2)


def startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue, main_branch):
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
        selectedSettings = selectedSettings.copy() if selectedSettings else {}
        selectedSettings["estimated_time"] = int(estimated_time_per_project)

    created_issue = createIssue(title, project_id, milestone, epic, iteration, selectedSettings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if onlyIssue:
        return created_issue

    created_branch = create_branch(project_id, created_issue, main_branch)
    created_merge_request = create_merge_request(
        project_id,
        created_branch,
        created_issue,
        selectedSettings.get("labels"),
        milestone,
        main_branch,
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


def process_report(text, minutes):
    from config import CONFIG

    try:
        incident_project_id = CONFIG.get("DEFAULT", "incident_project_id")
    except Exception:
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"
    selected_label = selectLabels("Department")
    incident_settings = {
        "labels": ["incident", "report"],
        "onlyIssue": True,
        "type": "incident",
    }

    if selected_label:
        incident_settings["labels"].append(selected_label)

    try:
        iteration = getActiveIteration()
        created_issue = createIssue(
            issue_title,
            incident_project_id,
            False,
            False,
            iteration,
            incident_settings,
        )
        issue_iid = created_issue["iid"]

        closeOpenedIssue(issue_iid, incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        import subprocess

        time_tracking_command = [
            "glab",
            "api",
            f"/projects/{incident_project_id}/issues/{issue_iid}/add_spent_time",
            "-f",
            f"duration={minutes}m",
        ]

        try:
            subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Added {minutes} minutes to issue time tracking.")
        except subprocess.CalledProcessError as error:
            print(f"Error adding time tracking: {str(error)}")

    except Exception as error:
        print(f"Error creating incident issue: {str(error)}")
