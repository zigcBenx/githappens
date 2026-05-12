import subprocess

import inquirer
import requests

from .. import config as settings
from .. import gitlab_api
from . import open_mr
from .create_issue import get_project_id


def add_reviewers_to_merge_request(reviewers=None):
    project_id = get_project_id()
    mr_id = open_mr.get_active_merge_request_id()
    requests.put(
        f"{settings.API_URL}/projects/{project_id}/merge_requests/{mr_id}",
        headers=gitlab_api.private_token_headers(),
        json={"reviewer_ids": reviewers if reviewers is not None else settings.REVIEWERS},
    )


def set_merge_request_to_auto_merge():
    project_id = get_project_id()
    mr_id = open_mr.get_active_merge_request_id()
    requests.put(
        f"{settings.API_URL}/projects/{project_id}/merge_requests/{mr_id}/merge",
        headers=gitlab_api.private_token_headers(),
        json={
            "id": project_id,
            "merge_request_iid": mr_id,
            "should_remove_source_branch": True,
            "merge_when_pipeline_succeeds": True,
            "auto_merge_strategy": "merge_when_pipeline_succeeds",
        },
    )


def track_issue_time():
    try:
        project_id = get_project_id()
        issue_id = open_mr.get_current_issue_id()
    except Exception as exc:
        print(f"Error getting issue details: {str(exc)}")
        return

    spent_time = inquirer.prompt(
        [
            inquirer.Text(
                "spent_time",
                message="How many minutes did you actually spend on this issue?",
                validate=lambda _, value: value.isdigit(),
            )
        ]
    )["spent_time"]

    time_tracking_command = [
        "glab",
        "api",
        f"/projects/{project_id}/issues/{issue_id}/notes",
        "-f",
        f"body=/spend {spent_time}m",
    ]

    try:
        subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except subprocess.CalledProcessError as exc:
        print(f"Error adding time tracking: {str(exc)}")
    except Exception as exc:
        print(f"Error tracking issue time: {str(exc)}")
