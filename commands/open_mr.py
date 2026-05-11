import subprocess
import webbrowser

import config
import gitlab_api as api


def open_merge_request_in_browser():
    try:
        merge_request_id = api.get_active_merge_request_id()
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True,
        ).strip()
        url = config.BASE_URL + "/" + remote_url.split(":")[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except (subprocess.CalledProcessError, TypeError, IndexError):
        return None
