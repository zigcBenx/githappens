import subprocess
import webbrowser

from config import CONFIG
from gitlab_api import get_active_merge_request_id


def open_merge_request_in_browser():
    try:
        merge_request_id = get_active_merge_request_id()
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True,
        ).strip()
        url = CONFIG.base_url + "/" + remote_url.split(":")[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None


# Backwards-compatible name.
openMergeRequestInBrowser = open_merge_request_in_browser
