import configparser
import subprocess

from config import API_URL
from interactive import getActiveIteration
from commands.create_issue import createIssue
from interactive import selectLabels


def process_report(text, minutes):
    # Get the incident project ID from config
    try:
        incident_project_id = config.get('DEFAULT', 'incident_project_id')
    except (configparser.NoOptionError, configparser.NoSectionError):
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"

    selected_label = selectLabels('Department')

    incident_settings = {
        'labels': ['incident', 'report'],
        'onlyIssue': True,
        'type': 'incident'
    }

    if selected_label:
        incident_settings['labels'].append(selected_label)

    try:
        # Create the incident issue
        iteration = getActiveIteration()
        created_issue = createIssue(issue_title, incident_project_id, False, False, iteration, incident_settings)
        issue_iid = created_issue['iid']

        closeOpenedIssue(issue_iid, incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        # Add time tracking to the issue
        time_tracking_command = [
            "glab", "api",
            f"/projects/{incident_project_id}/issues/{issue_iid}/add_spent_time",
            "-f", f"duration={minutes}m"
        ]

        try:
            subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Added {minutes} minutes to issue time tracking.")
        except subprocess.CalledProcessError as e:
            print(f"Error adding time tracking: {str(e)}")

    except Exception as e:
        print(f"Error creating incident issue: {str(e)}")

def closeOpenedIssue(issue_iid, project_id):
    issue_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        '-X', 'PUT',
        '-f', 'state_event=close'
    ]
    try:
        subprocess.run(issue_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {str(e)}")

