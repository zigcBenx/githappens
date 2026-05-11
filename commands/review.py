import interactive
from commands.open_mr import get_active_merge_request


def get_current_issue_id(api):
    merge_request, _project_id = get_active_merge_request(api)
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time(api, project_id, issue_id):
    spent_time = interactive.prompt_spent_time()

    try:
        api.add_time_tracking_note(project_id, issue_id, spent_time)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except Exception as error:
        print(f"Error tracking issue time: {str(error)}")


def submit_for_review(api, settings, select_reviewers: bool = False, auto_merge: bool = False):
    try:
        merge_request, project_id = get_active_merge_request(api)
        issue_id = merge_request["description"].replace('"', "").replace("#", "").split()[1]
    except Exception as error:
        print(f"Error getting issue details: {str(error)}")
        return

    track_issue_time(api, project_id, issue_id)

    reviewers = None
    if select_reviewers:
        reviewers = interactive.choose_reviewers_manually(api, settings.reviewers)
    api.add_reviewers_to_merge_request(project_id, merge_request["iid"], reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        run_review_for_mr(project_id, merge_request["iid"], settings.gitlab_token, settings.api_url)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        api.set_merge_request_to_auto_merge(project_id, merge_request["iid"])
