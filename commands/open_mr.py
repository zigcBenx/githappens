import webbrowser

import git_utils
from commands.create_issue import resolve_project_id


def get_active_merge_request(api):
    project_id = resolve_project_id(api)
    branch_name = git_utils.get_current_branch()
    return api.get_merge_request_for_branch(project_id, branch_name), project_id


def get_active_merge_request_id(api):
    merge_request, _project_id = get_active_merge_request(api)
    return merge_request["iid"]


def find_merge_request_id_by_branch(api, branch_name):
    project_id = resolve_project_id(api)
    return api.get_merge_request_for_branch(project_id, branch_name)["iid"]


def open_merge_request_in_browser(api, settings):
    try:
        merge_request_id = get_active_merge_request_id(api)
        remote_url = git_utils.get_remote_origin_url()
        url = settings.base_url + "/" + remote_url.split(":")[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except Exception:
        return None
