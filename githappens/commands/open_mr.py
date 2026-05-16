from __future__ import annotations

import subprocess
import webbrowser

from ..config import AppConfig
from ..git_utils import get_current_branch
from ..gitlab_api import find_merge_request_id_by_branch


def open_merge_request_in_browser(config: AppConfig) -> None:
    try:
        merge_request_id = find_merge_request_id_by_branch(config, get_current_branch())
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = f"{config.base_url}/{remote_url.split(':')[1][:-4]}"
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return
