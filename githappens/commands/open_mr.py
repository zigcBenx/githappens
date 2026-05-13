import subprocess
from urllib.parse import urlparse
import webbrowser

from .. import config, git_utils, gitlab_api
from .create_issue import get_project_id


def get_active_merge_request_id():
    branch_to_find = git_utils.get_current_branch()
    return find_merge_request_id_by_branch(branch_to_find)


def find_merge_request_id_by_branch(branch_name):
    merge_request = get_merge_request_for_branch(branch_name)
    if not merge_request:
        print(f"No active merge request found for branch {branch_name}.")
        return None
    return merge_request["iid"]


def get_merge_request_for_branch(branch_name):
    project_id = get_project_id()
    return gitlab_api.get_merge_request_for_branch(project_id, branch_name)


def open_merge_request_in_browser():
    try:
        merge_request_id = get_active_merge_request_id()
        if not merge_request_id:
            return None
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
        project_path = project_path_from_remote(remote_url)
        if not project_path:
            print(f"Could not parse GitLab remote URL: {remote_url}")
            return None
        url = config.BASE_URL + "/" + project_path
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None


def project_path_from_remote(remote_url):
    if remote_url.startswith("git@"):
        _, path = remote_url.split(":", 1)
        return path.removesuffix(".git")

    parsed = urlparse(remote_url)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return parsed.path.strip("/").removesuffix(".git")

    return None
