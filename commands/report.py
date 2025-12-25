import configparser
import subprocess

from config import get_config
from gitlab_api import execute_issue_create, close_opened_issue
from interactive import get_active_iteration, select_labels


def process_report(text, minutes):
    config = get_config()
    # Get the incident project ID from config
    try:
        incident_project_id = config.get("DEFAULT", "incident_project_id")
    except (configparser.NoOptionError, configparser.NoSectionError):
        print("Error: incident_project_id not found in config.ini")
        print(
            "Please add your incident project ID to configs/config.ini under [DEFAULT] section:"
        )
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
        if isinstance(selected_label, list):
            incident_settings["labels"].extend(selected_label)
        else:
            incident_settings["labels"].append(selected_label)

    try:
        # Create the incident issue
        iteration = get_active_iteration()
        created_issue = execute_issue_create(
            incident_project_id,
            issue_title,
            incident_settings.get("labels"),
            False,
            False,
            iteration,
            None,
            None,
            "incident",
        )
        issue_iid = created_issue["iid"]

        close_opened_issue(issue_iid, incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        # Add time tracking to the issue
        time_tracking_command = [
            "glab",
            "api",
            f"/projects/{incident_project_id}/issues/{issue_iid}/add_spent_time",
            "-f",
            f"duration={minutes}m",
        ]

        try:
            subprocess.run(
                time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print(f"Added {minutes} minutes to issue time tracking.")
        except subprocess.CalledProcessError as e:
            print(f"Error adding time tracking: {str(e)}")

    except Exception as e:
        print(f"Error creating incident issue: {str(e)}")


def handle_report_command(parts):
    if len(parts) != 3:
        print('Invalid report format. Use: gh report "text" minutes')
        return

    text = parts[1]
    try:
        minutes = int(parts[2].strip())
        process_report(text, minutes)
    except ValueError:
        print("Invalid minutes. Please provide a valid number.")
