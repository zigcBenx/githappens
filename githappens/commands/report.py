import configparser
import subprocess

from .. import config, gitlab_api
from .create_issue import create_issue, get_active_iteration, select_labels


def close_opened_issue(issue_iid, project_id):
    gitlab_api.close_opened_issue(issue_iid, project_id)


def process_report(text, minutes):
    try:
        incident_project_id = config.config.get("DEFAULT", "incident_project_id")
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
        iteration = get_active_iteration()
        created_issue = create_issue(
            issue_title, incident_project_id, False, False, iteration, incident_settings
        )
        issue_iid = created_issue["iid"]

        close_opened_issue(issue_iid, incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        time_tracking_command = [
            "glab",
            "api",
            f"/projects/{incident_project_id}/issues/{issue_iid}/add_spent_time",
            "-f",
            f"duration={minutes}m",
        ]

        try:
            subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"Added {minutes} minutes to issue time tracking.")
        except subprocess.CalledProcessError as error:
            print(f"Error adding time tracking: {str(error)}")
    except Exception as error:
        print(f"Error creating incident issue: {str(error)}")
