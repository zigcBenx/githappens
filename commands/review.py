import subprocess

from config import CONFIG
from git_utils import get_current_branch
from gitlab_api import (
    add_reviewers_to_merge_request,
    get_active_merge_request_id,
    get_merge_request_for_branch,
    get_project_id,
    set_merge_request_to_auto_merge,
)
from interactive import choose_reviewers_manually, prompt_spent_time


def get_current_issue_id():
    merge_request = get_merge_request_for_branch(get_current_branch())
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time():
    try:
        project_id = get_project_id()
        issue_id = get_current_issue_id()
    except Exception as error:
        print(f"Error getting issue details: {str(error)}")
        return

    spent_time = prompt_spent_time()
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
    except subprocess.CalledProcessError as error:
        print(f"Error adding time tracking: {str(error)}")
    except Exception as error:
        print(f"Error tracking issue time: {str(error)}")


def run_review_workflow(select_reviewers=False, auto_merge=False):
    track_issue_time()
    reviewers = choose_reviewers_manually() if select_reviewers else None
    add_reviewers_to_merge_request(reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = get_project_id()
        mr_id = get_active_merge_request_id()
        run_review_for_mr(project_id, mr_id, CONFIG.gitlab_token, CONFIG.api_url)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        set_merge_request_to_auto_merge()


# Backwards-compatible names.
getCurrentIssueId = get_current_issue_id
track_issue_time = track_issue_time
