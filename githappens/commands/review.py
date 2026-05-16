from ..config import get_settings
from ..git_utils import get_current_branch
from ..gitlab_api import (
    get_merge_request_for_branch,
    get_project_id,
    get_reviewers_with_names,
    put_merge_request_auto_merge,
    put_merge_request_reviewers,
)
from ..interactive import prompt_checkbox, prompt_text


def get_current_issue_id():
    mr = get_merge_request_for_branch(get_current_branch())
    return mr["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time():
    try:
        project_id = get_project_id()
        issue_id = get_current_issue_id()
    except Exception as error:
        print(f"Error getting issue details: {str(error)}")
        return

    spent_time = prompt_text(
        "spent_time",
        message="How many minutes did you actually spend on this issue?",
        validate=lambda _, value: value.isdigit(),
    )["spent_time"]

    import subprocess

    time_tracking_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_id}/notes",
        "-f", f"body=/spend {spent_time}m",
    ]
    try:
        subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except subprocess.CalledProcessError as error:
        print(f"Error adding time tracking: {str(error)}")
    except Exception as error:
        print(f"Error tracking issue time: {str(error)}")


def choose_reviewers_manually():
    choices = [(name, str(reviewer_id)) for name, reviewer_id in get_reviewers_with_names()]
    answers = prompt_checkbox("selected_reviewers", message="Select reviewers", choices=choices)
    if answers and "selected_reviewers" in answers:
        return [int(reviewer) for reviewer in answers["selected_reviewers"]]
    return []


def add_reviewers_to_merge_request(reviewers=None):
    project_id = get_project_id()
    mr_id = get_merge_request_for_branch(get_current_branch())["iid"]
    put_merge_request_reviewers(project_id, mr_id, reviewers)


def set_merge_request_to_auto_merge():
    project_id = get_project_id()
    mr_id = get_merge_request_for_branch(get_current_branch())["iid"]
    put_merge_request_auto_merge(project_id, mr_id)


def review_command(select=False, auto_merge=False):
    track_issue_time()
    reviewers = choose_reviewers_manually() if select else None
    add_reviewers_to_merge_request(reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = get_project_id()
        mr_id = get_merge_request_for_branch(get_current_branch())["iid"]
        run_review_for_mr(project_id, mr_id, get_settings().gitlab_token, get_settings().api_url)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        set_merge_request_to_auto_merge()
