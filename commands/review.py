import subprocess

import gitlab_api as api
import interactive


def track_issue_time():
    try:
        project_id = api.get_project_id()
        issue_id = api.get_current_issue_id()
    except Exception as error:
        print(f"Error getting issue details: {str(error)}")
        return

    spent_time = interactive.prompt_spent_time()
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


def review_merge_request(select_reviewers=False, auto_merge=False):
    track_issue_time()
    reviewers = None
    if select_reviewers:
        reviewers = interactive.choose_reviewers_manually(api.fetch_reviewer_choices())
    api.add_reviewers_to_merge_request(reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = api.get_project_id()
        merge_request_id = api.get_active_merge_request_id()
        from config import API_URL, GITLAB_TOKEN

        run_review_for_mr(project_id, merge_request_id, GITLAB_TOKEN, API_URL)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        api.set_merge_request_to_auto_merge()
