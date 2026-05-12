"""Open the active merge request in the browser."""
import subprocess
import webbrowser

import config
import git_utils
from commands.merge_request import get_active_merge_request_id


def open_merge_request_in_browser():
    try:
        merge_request_id = get_active_merge_request_id()
        remote_url = git_utils.get_remote_origin_url()
        url = config.BASE_URL + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None
