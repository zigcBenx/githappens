import configparser
import subprocess

from .. import config as settings
from .. import gitlab_api
from ..interactive import get_active_iteration, select_labels
from .create_issue import create_issue


def process_report(text, minutes):
    try:
        incident_project_id = settings.config.get("DEFAULT", "incident_project_id")
    except (configparser.NoOptionError, configparser.NoSectionError):
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"
    selected_label = select_labels("Department")
    incident_settings = {"labels": ["incident", "report"], "onlyIssue": True, "type": "incident"}

    if selected_label:
        incident_settings["labels"].append(selected_label)

    try:
        created_issue = create_issue(
            issue_title,
            incident_project_id,
            False,
            False,
            get_active_iteration(),
            incident_settings,
        )
        issue_iid = created_issue["iid"]
        gitlab_api.close_opened_issue(issue_iid, incident_project_id)
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
            subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Added {minutes} minutes to issue time tracking.")
        except subprocess.CalledProcessError as exc:
            print(f"Error adding time tracking: {str(exc)}")
    except Exception as exc:
        print(f"Error creating incident issue: {str(exc)}")

