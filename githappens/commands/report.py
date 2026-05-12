import subprocess

from .. import gitlab_api, interactive
from .create_issue import create_issue


def process_report(ctx, text, minutes):
    incident_project_id = ctx.settings.incident_project_id
    if not incident_project_id:
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT]:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"
    selected_label = interactive.select_labels(ctx, "Department")

    incident_settings = {
        "labels": ["incident", "report"],
        "onlyIssue": True,
        "type": "incident",
    }
    if selected_label:
        incident_settings["labels"].append(selected_label)

    try:
        iteration = interactive.get_active_iteration(ctx)
        created_issue = create_issue(
            ctx,
            issue_title,
            incident_project_id,
            False,
            False,
            iteration,
            incident_settings,
        )
        issue_iid = created_issue["iid"]

        gitlab_api.close_opened_issue(incident_project_id, issue_iid)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        command = [
            "glab",
            "api",
            f"/projects/{incident_project_id}/issues/{issue_iid}/add_spent_time",
            "-f",
            f"duration={minutes}m",
        ]
        try:
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Added {minutes} minutes to issue time tracking.")
        except subprocess.CalledProcessError as exc:
            print(f"Error adding time tracking: {str(exc)}")
    except Exception as exc:
        print(f"Error creating incident issue: {str(exc)}")
