import subprocess
import webbrowser

from config import BASE_URL
from gitlab_api import getActiveMergeRequestId
from git_utils import getCurrentBranch


def openMergeRequestInBrowser():
    try:
        merge_request_id = getActiveMergeRequestId()
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = BASE_URL + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None

