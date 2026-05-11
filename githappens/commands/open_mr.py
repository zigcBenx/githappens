import subprocess
import webbrowser

from ..config import get_settings
from ..git_utils import get_current_branch
from ..gitlab_api import get_active_merge_request_id


def _remote_path(remote_url: str) -> str:
    if remote_url.startswith("http"):
        return remote_url.rstrip("/").removesuffix(".git").split("/", 3)[-1]
    return remote_url.split(":", 1)[1].removesuffix(".git")


def open_merge_request_in_browser():
    try:
        merge_request_id = get_active_merge_request_id(get_current_branch())
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = get_settings().base_url + "/" + _remote_path(remote_url)
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None


openMergeRequestInBrowser = open_merge_request_in_browser

