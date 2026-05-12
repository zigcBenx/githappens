import subprocess
import webbrowser

from .. import config as settings
from .. import git_utils, gitlab_api
from .create_issue import get_project_id


def get_merge_request_for_branch(branch_name):
    return gitlab_api.get_merge_request_for_branch(get_project_id(), branch_name)


def find_merge_request_id_by_branch(branch_name):
    return get_merge_request_for_branch(branch_name)["iid"]


def get_active_merge_request_id():
    return find_merge_request_id_by_branch(git_utils.get_current_branch())


def open_merge_request_in_browser():
    try:
        merge_request_id = get_active_merge_request_id()
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = settings.BASE_URL + "/" + remote_url.split(":")[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None


def get_current_issue_id():
    merge_request = get_merge_request_for_branch(git_utils.get_current_branch())
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]

