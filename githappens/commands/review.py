import subprocess

from ..config import get_settings
from ..git_utils import get_current_branch
from ..gitlab_api import (
    add_reviewers_to_merge_request,
    get_active_merge_request_id,
    get_merge_request_for_branch,
    get_project_id,
    set_merge_request_to_auto_merge,
)
from ..interactive import choose_reviewers_manually
from ..templates import get_reviewers


def get_current_issue_id():
    merge_request = get_merge_request_for_branch(get_current_branch())
    return merge_request["description"].replace("\"", "").replace("#", "").split()[1]


def track_issue_time():
    import inquirer

    try:
        project_id = get_project_id()
        issue_id = get_current_issue_id()
    except Exception as error:
        print(f"Error getting issue details: {str(error)}")
        return

    spent_time = inquirer.prompt([
        inquirer.Text(
            "spent_time",
            message="How many minutes did you actually spend on this issue?",
            validate=lambda _, value: value.isdigit(),
        )
    ])["spent_time"]

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


def review_merge_request(select_reviewers=False, auto_merge=False):
    settings = get_settings()
    branch_name = get_current_branch()

    track_issue_time()
    reviewers = None
    if select_reviewers:
        reviewers = choose_reviewers_manually(get_reviewers(), settings.api_url, settings.gitlab_token)
    add_reviewers_to_merge_request(branch_name, reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = get_project_id()
        mr_id = get_active_merge_request_id(branch_name)
        run_review_for_mr(project_id, mr_id, settings.gitlab_token, settings.api_url)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        set_merge_request_to_auto_merge(branch_name)


getCurrentIssueId = get_current_issue_id
chooseReviewersManually = choose_reviewers_manually
