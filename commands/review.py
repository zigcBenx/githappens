import gitlab_api
import git_utils
import interactive


def get_active_merge_request_id():
    branch_to_find = git_utils.get_current_branch()
    return find_merge_request_id_by_branch(branch_to_find)


def find_merge_request_id_by_branch(branch_name):
    return get_merge_request_for_branch(branch_name)["iid"]


def get_merge_request_for_branch(branch_name):
    project_id = git_utils.resolve_project_id()
    return gitlab_api.get_merge_request_for_branch(project_id, branch_name)


def get_current_issue_id():
    merge_request = get_merge_request_for_branch(git_utils.get_current_branch())
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time():
    try:
        project_id = git_utils.resolve_project_id()
        issue_id = get_current_issue_id()
    except Exception as e:
        print(f"Error getting issue details: {str(e)}")
        return

    spent_time = interactive.prompt_spent_time()

    try:
        gitlab_api.add_issue_time_note(project_id, issue_id, spent_time)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except Exception as e:
        print(f"Error tracking issue time: {str(e)}")


def choose_reviewers_manually():
    return interactive.choose_reviewers_manually(get_user=gitlab_api.get_user)


def add_reviewers_to_merge_request(reviewers=None):
    project_id = git_utils.resolve_project_id()
    mr_id = get_active_merge_request_id()
    gitlab_api.add_reviewers_to_merge_request(project_id, mr_id, reviewers)


def set_merge_request_to_auto_merge():
    project_id = git_utils.resolve_project_id()
    mr_id = get_active_merge_request_id()
    gitlab_api.set_merge_request_to_auto_merge(project_id, mr_id)


def run_review_command(select=False, auto_merge=False):
    track_issue_time()
    reviewers = choose_reviewers_manually() if select else None
    add_reviewers_to_merge_request(reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = git_utils.resolve_project_id()
        mr_id = get_active_merge_request_id()
        from config import API_URL, GITLAB_TOKEN

        run_review_for_mr(project_id, mr_id, GITLAB_TOKEN, API_URL)
    except Exception as e:
        print(f"AI review skipped: {e}")

    if auto_merge:
        set_merge_request_to_auto_merge()
