import subprocess
import re

from .. import gitlab_api, git_utils, interactive, templates
from .create_issue import get_project_id
from .open_mr import get_active_merge_request_id, get_merge_request_for_branch


def choose_reviewers_manually():
    return interactive.choose_reviewers_manually(templates.get_reviewers(), gitlab_api.get_user)


def add_reviewers_to_merge_request(reviewers=None):
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    gitlab_api.add_reviewers_to_merge_request(
        project_id,
        mr_id,
        reviewers if reviewers is not None else templates.get_reviewers(),
    )


def set_merge_request_to_auto_merge():
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    gitlab_api.set_merge_request_to_auto_merge(project_id, mr_id)


def get_current_issue_id():
    mr = get_merge_request_for_branch(git_utils.get_current_branch())
    if not mr:
        raise ValueError("No merge request found for the current branch.")
    match = re.search(r"Closes\s+#(\d+)", mr.get("description", "").replace('"', ""))
    if not match:
        raise ValueError("Could not find an issue reference in the merge request description.")
    return match.group(1)


def track_issue_time():
    try:
        project_id = get_project_id()
        issue_id = get_current_issue_id()
    except Exception as error:
        print(f"Error getting issue details: {str(error)}")
        return

    spent_time = interactive.prompt_spent_time()

    try:
        gitlab_api.add_issue_spent_time(project_id, issue_id, spent_time)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except subprocess.CalledProcessError as error:
        print(f"Error adding time tracking: {str(error)}")
    except Exception as error:
        print(f"Error tracking issue time: {str(error)}")


def review_flow(auto_merge=False, select=False):
    track_issue_time()
    reviewers = choose_reviewers_manually() if select else None
    add_reviewers_to_merge_request(reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = get_project_id()
        mr_id = get_active_merge_request_id()
        from .. import config

        run_review_for_mr(project_id, mr_id, config.GITLAB_TOKEN, config.API_URL)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        set_merge_request_to_auto_merge()
