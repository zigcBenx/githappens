"""Merge request operations: lookups, reviewers, auto-merge."""
import git_utils
import gitlab_api
from project import get_project_id


def get_merge_request_for_branch(branch_name):
    project_id = get_project_id()
    merge_requests = gitlab_api.get_merge_requests(project_id, {"source_branch": branch_name})
    if not merge_requests:
        return None
    for mr in merge_requests:
        if mr["source_branch"] == branch_name:
            return mr
    return None


def find_merge_request_id_by_branch(branch_name):
    return get_merge_request_for_branch(branch_name)['iid']


def get_active_merge_request_id():
    return find_merge_request_id_by_branch(git_utils.get_current_branch())


def get_current_issue_id():
    mr = get_merge_request_for_branch(git_utils.get_current_branch())
    return mr['description'].replace('"', '').replace('#', '').split()[1]


def add_reviewers_to_merge_request(reviewers=None):
    import config
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    data = {"reviewer_ids": reviewers if reviewers is not None else config.REVIEWERS}
    gitlab_api.update_merge_request(project_id, mr_id, data)


def set_merge_request_to_auto_merge():
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    gitlab_api.merge_merge_request(project_id, mr_id, data)
