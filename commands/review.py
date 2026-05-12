import subprocess

from config import API_URL, GITLAB_TOKEN, REVIEWERS
from git_utils import getCurrentBranch
from gitlab_api import addReviewersToMergeRequest, getMergeRequestForBranch, setMergeRequestToAutoMerge
from interactive import chooseReviewersManually

from .create_issue import get_project_id
from .open_mr import getActiveMergeRequestId


def getCurrentIssueId():
    merge_request = getMergeRequestForBranch(get_project_id(), getCurrentBranch())
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time():
    try:
        project_id = get_project_id()
        issue_id = getCurrentIssueId()
    except Exception as error:
        print(f"Error getting issue details: {str(error)}")
        return

    import inquirer

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
    except subprocess.CalledProcessError as error:
        print(f"Error adding time tracking: {str(error)}")
    except Exception as error:
        print(f"Error tracking issue time: {str(error)}")


def review_current_merge_request(auto_merge=False, select=False):
    track_issue_time()
    reviewers = chooseReviewersManually() if select else REVIEWERS
    project_id = get_project_id()
    mr_id = getActiveMergeRequestId()
    addReviewersToMergeRequest(project_id, mr_id, reviewers)

    try:
        from ai_code_review import run_review_for_mr

        run_review_for_mr(project_id, mr_id, GITLAB_TOKEN, API_URL)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        setMergeRequestToAutoMerge(project_id, mr_id)
