from __future__ import annotations

import subprocess
import webbrowser

from .. import git_utils, gitlab_api, interactive
from ..config import AppConfig


def get_active_merge_request_id(config: AppConfig):
    branch = git_utils.get_current_branch()
    project_id = interactive.get_project_id(config)
    return gitlab_api.get_merge_request_for_branch(config, project_id, branch)["iid"]


def open_merge_request_in_browser(config: AppConfig):
    try:
        merge_request_id = get_active_merge_request_id(config)
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = config.base_url + "/" + remote_url.split(":")[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None

