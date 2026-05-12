"""Review workflow: time tracking, reviewers, AI review."""
import gitlab_api
import interactive
from commands.merge_request import (
    add_reviewers_to_merge_request,
    get_active_merge_request_id,
    get_current_issue_id,
    set_merge_request_to_auto_merge,
)
from project import get_project_id


def track_issue_time():
    try:
        project_id = get_project_id()
        issue_id = get_current_issue_id()
    except Exception as e:
        print(f"Error getting issue details: {str(e)}")
        return

    spent_time = interactive.prompt_spent_time()

    try:
        gitlab_api.add_issue_note(project_id, issue_id, f"/spend {spent_time}m")
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except Exception as e:
        print(f"Error tracking issue time: {str(e)}")


def run_review(auto_merge=False, manual_select=False):
    track_issue_time()

    reviewers = interactive.choose_reviewers_manually() if manual_select else None
    add_reviewers_to_merge_request(reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr
        import config
        project_id = get_project_id()
        mr_id = get_active_merge_request_id()
        run_review_for_mr(project_id, mr_id, config.GITLAB_TOKEN, config.API_URL)
    except Exception as e:
        print(f"AI review skipped: {e}")

    if auto_merge:
        set_merge_request_to_auto_merge()
