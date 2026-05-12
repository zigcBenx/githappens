#!/usr/bin/env python3
import config
import gitlab_api
import interactive


def run(text, minutes):
    incident_project_id = config.config.get('DEFAULT', 'incident_project_id', fallback=None)
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
        iteration = gitlab_api.get_active_iteration()
        created_issue = gitlab_api.execute_issue_create(
            incident_project_id,
            issue_title,
            incident_settings.get('labels'),
            False,
            False,
            iteration,
            None,
            None,
            incident_settings.get('type'),
        )
        issue_iid = created_issue['iid']
        gitlab_api.close_opened_issue(issue_iid, incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")
        gitlab_api.add_spent_time(incident_project_id, issue_iid, minutes)
        print(f"Added {minutes} minutes to issue time tracking.")
    except Exception as e:
        print(f"Error creating incident issue: {str(e)}")
