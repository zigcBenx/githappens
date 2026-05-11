from __future__ import annotations

from githappens.git_utils import get_current_branch
from githappens.gitlab_api import GitLabApiError
from githappens.interactive import prompt_spent_time


def get_merge_request_for_current_branch(client, project_id):
    branch_name = get_current_branch()
    merge_request = client.get_merge_request_for_branch(project_id, branch_name)
    if not merge_request:
        raise GitLabApiError(f"No open merge request found for branch '{branch_name}'.")
    return merge_request


def get_current_issue_id(client, project_id) -> str:
    merge_request = get_merge_request_for_current_branch(client, project_id)
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time(client, project_id):
    try:
        issue_id = get_current_issue_id(client, project_id)
    except Exception as exc:
        print(f"Error getting issue details: {exc}")
        return

    spent_time = prompt_spent_time()
    try:
        client.add_issue_note(project_id, issue_id, f"/spend {spent_time}m")
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except Exception as exc:
        print(f"Error tracking issue time: {exc}")


def add_reviewers_to_merge_request(runtime, client, project_id, reviewers=None):
    merge_request = get_merge_request_for_current_branch(client, project_id)
    reviewer_ids = reviewers if reviewers is not None else runtime.reviewers
    client.update_merge_request_reviewers(project_id, merge_request["iid"], reviewer_ids)


def set_merge_request_to_auto_merge(client, project_id):
    merge_request = get_merge_request_for_current_branch(client, project_id)
    client.enable_auto_merge(project_id, merge_request["iid"])
