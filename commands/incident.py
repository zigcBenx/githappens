"""Incident report workflow."""
import config
import gitlab_api
import interactive
from commands.create_issue import create_issue


def process_report(text, minutes):
    incident_project_id = config.get_incident_project_id()
    if not incident_project_id:
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"
    selected_label = interactive.select_labels('Department')

    incident_settings = {
        'labels': ['incident', 'report'],
        'onlyIssue': True,
        'type': 'incident',
    }
    if selected_label:
        incident_settings['labels'].append(selected_label)

    try:
        iteration = interactive.get_active_iteration()
        created_issue = create_issue(
            issue_title, incident_project_id, False, False, iteration, incident_settings,
        )
        issue_iid = created_issue['iid']

        gitlab_api.close_issue(incident_project_id, issue_iid)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        if gitlab_api.add_spent_time(incident_project_id, issue_iid, minutes):
            print(f"Added {minutes} minutes to issue time tracking.")

    except Exception as e:
        print(f"Error creating incident issue: {str(e)}")
