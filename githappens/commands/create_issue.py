import json
import re
import subprocess

import inquirer

from .. import config as settings
from .. import git_utils, gitlab_api
from ..interactive import enter_project_id


def get_project_id():
    project_link = git_utils.get_project_link_from_current_dir()
    if project_link == -1:
        return enter_project_id()

    all_projects = gitlab_api.get_all_projects(project_link)
    for project in all_projects:
        if project.get("ssh_url_to_repo") == project_link:
            return project.get("id")
    return None


def create_issue(title, project_id, milestone_id, epic, iteration, settings_template):
    if settings_template:
        issue_type = settings_template.get("type") or "issue"
        return execute_issue_create(
            project_id,
            title,
            settings_template.get("labels"),
            milestone_id,
            epic,
            iteration,
            settings_template.get("weight"),
            settings_template.get("estimated_time"),
            issue_type,
        )
    print("No settings in template")
    raise SystemExit(2)


def execute_issue_create(project_id, title, labels, milestone_id, epic, iteration, weight, estimated_time, issue_type="issue"):
    labels = ",".join(labels) if isinstance(labels, list) else labels
    assignee_id = gitlab_api.get_authorized_user()["id"]
    issue_command = [
        "glab",
        "api",
        f"/projects/{str(project_id)}/issues",
        "-f",
        f"title={title}",
        "-f",
        f"assignee_ids={assignee_id}",
        "-f",
        f"issue_type={issue_type}",
    ]

    optional_fields = {
        "labels": labels,
        "weight": str(weight) if weight else None,
        "milestone_id": str(milestone_id) if milestone_id else None,
    }
    for field, value in optional_fields.items():
        if value:
            issue_command.extend(["-f", f"{field}={value}"])

    if epic:
        issue_command.extend(["-f", f"epic_id={str(epic['id'])}"])

    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    issue_command.extend(["-f", f"description={description}"])

    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_branch(project_id, issue):
    issue_id = str(issue["iid"])
    title = re.sub("\\s+", "-", issue["title"]).lower()
    title = issue_id + "-" + title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    branch_output = subprocess.check_output(
        [
            "glab",
            "api",
            f"/projects/{str(project_id)}/repository/branches",
            "-f",
            f"branch={title}",
            "-f",
            f"ref={settings.MAIN_BRANCH}",
            "-f",
            f"issue_iid={issue_id}",
        ]
    )
    return json.loads(branch_output.decode())


def create_merge_request(project_id, branch, issue, labels, milestone_id):
    issue_id = str(issue["iid"])
    branch_name = branch["name"]
    labels = ",".join(labels) if isinstance(labels, list) else labels
    assignee_id = gitlab_api.get_authorized_user()["id"]
    merge_request_command = [
        "glab",
        "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f",
        f"title={issue['title']}",
        "-f",
        f"description=\"Closes #{issue_id}\"",
        "-f",
        f"source_branch={branch_name}",
        "-f",
        f"target_branch={settings.MAIN_BRANCH}",
        "-f",
        f"issue_iid={issue_id}",
        "-f",
        f"assignee_ids={assignee_id}",
    ]

    if settings.SQUASH_COMMITS:
        merge_request_command.extend(["-f", "squash=true"])
    if settings.DELETE_BRANCH:
        merge_request_command.extend(["-f", "remove_source_branch=true"])
    if labels:
        merge_request_command.extend(["-f", f"labels={labels}"])
    if milestone_id:
        merge_request_command.extend(["-f", f"milestone_id={str(milestone_id)}"])

    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())


def start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue):
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

    created_issue = create_issue(title, project_id, milestone, epic, iteration, selected_settings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = create_branch(project_id, created_issue)
    created_merge_request = create_merge_request(
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

