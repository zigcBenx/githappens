import webbrowser

from config import BASE_URL
from git_utils import getCurrentBranch
from gitlab_api import getMergeRequestForBranch

from .create_issue import get_project_id


def openMergeRequestInBrowser():
    try:
        merge_request_id = getActiveMergeRequestId()
        import subprocess

        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
        url = BASE_URL + "/" + remote_url.split(":")[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except Exception:
        return None


def getActiveMergeRequestId():
    branch_to_find = getCurrentBranch()
    return find_merge_request_id_by_branch(branch_to_find)


def find_merge_request_id_by_branch(branch_name):
    merge_request = getMergeRequestForBranch(get_project_id(), branch_name)
    return merge_request["iid"]
