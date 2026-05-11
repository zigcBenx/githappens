from __future__ import annotations

import configparser
import subprocess

from ..config import AppConfig
from ..gitlab_api import add_spent_time, close_opened_issue, create_issue, get_active_iteration, get_labels_of_group
from ..interactive import select_labels


def process_report(config: AppConfig, text: str, minutes: int) -> None:
    parser = configparser.ConfigParser()
    parser.read(config.base_dir / "configs" / "config.ini")
    try:
        incident_project_id = parser.get("DEFAULT", "incident_project_id")
    except Exception:
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"
    selected_label = select_labels(get_labels_of_group(config, "Department"))
    incident_settings = {
        "labels": ["incident", "report"],
        "onlyIssue": True,
        "type": "incident",
    }
    if selected_label:
        incident_settings["labels"].append(selected_label)

    try:
        created_issue = create_issue(config, issue_title, incident_project_id, False, False, get_active_iteration(config), incident_settings)
        close_opened_issue(config, created_issue["iid"], incident_project_id)
        print(f"Incident issue #{created_issue['iid']} created successfully.")
        print(f"Title: {issue_title}")
        add_spent_time(incident_project_id, created_issue["iid"], minutes)
        print(f"Added {minutes} minutes to issue time tracking.")
    except subprocess.CalledProcessError as error:
        print(f"Error creating incident issue: {str(error)}")
    except Exception as error:
        print(f"Error creating incident issue: {str(error)}")
