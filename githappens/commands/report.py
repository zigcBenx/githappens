from __future__ import annotations

from .. import gitlab_api, interactive
from ..config import AppConfig
from .create_issue import create_issue


def process_report(config: AppConfig, text: str, minutes: int):
    if not config.incident_project_id:
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"
    selected_label = interactive.select_labels(config, "Department")
    incident_settings = {"labels": ["incident", "report"], "onlyIssue": True, "type": "incident"}
    if selected_label:
        incident_settings["labels"].append(selected_label)

    try:
        iteration = interactive.get_active_iteration(config)
        created_issue = create_issue(
            config,
            issue_title,
            config.incident_project_id,
            False,
            False,
            iteration,
            incident_settings,
        )
        issue_iid = created_issue["iid"]
        gitlab_api.close_issue(config.incident_project_id, issue_iid)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        try:
            gitlab_api.add_spent_time(config.incident_project_id, issue_iid, minutes)
            print(f"Added {minutes} minutes to issue time tracking.")
        except Exception as e:
            print(f"Error adding time tracking: {str(e)}")
    except Exception as e:
        print(f"Error creating incident issue: {str(e)}")

