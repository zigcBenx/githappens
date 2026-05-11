import configparser
import subprocess

import config
import gitlab_api as api
import interactive


def process_report(text, minutes):
    try:
        incident_project_id = config.CONFIG.get("DEFAULT", "incident_project_id")
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
        iteration = api.get_active_iteration()
        created_issue = api.create_issue(
            issue_title,
            incident_project_id,
            False,
            False,
            iteration,
            incident_settings,
        )
        issue_iid = created_issue["iid"]
        api.close_opened_issue(issue_iid, incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        time_tracking_command = [
            "glab",
            "api",
            f"/projects/{incident_project_id}/issues/{issue_iid}/add_spent_time",
            "-f",
            f"duration={minutes}m",
        ]
        subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Added {minutes} minutes to issue time tracking.")
    except Exception as error:
        print(f"Error creating incident issue: {str(error)}")


def select_labels(search, multiple=False):
    labels = api.get_labels_of_group(search)
    return interactive.select_labels([label["name"] for label in labels], multiple=multiple)
