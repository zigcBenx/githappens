import subprocess
import webbrowser

from ..config import get_settings
from ..git_utils import get_current_branch
from ..gitlab_api import find_merge_request_id_by_branch


def get_active_merge_request_id():
    return find_merge_request_id_by_branch(get_current_branch())


def open_merge_request_in_browser():
    try:
        merge_request_id = get_active_merge_request_id()
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = get_settings().base_url + "/" + remote_url.split(":")[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None
