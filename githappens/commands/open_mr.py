from __future__ import annotations

import subprocess
import webbrowser

from githappens import git_utils
from githappens.config import AppConfig
from githappens.gitlab_api import GitLabApi
from githappens.commands.create_issue import resolve_project_id


def get_merge_request_for_branch(api: GitLabApi, branch_name: str) -> dict | None:
    project_id = resolve_project_id(api)
    for merge_request in api.get_merge_requests_for_branch(project_id, branch_name):
        if merge_request["source_branch"] == branch_name:
            return merge_request
    return None


def get_active_merge_request_id(api: GitLabApi) -> int:
    merge_request = get_merge_request_for_branch(api, git_utils.get_current_branch())
    if not merge_request:
        raise RuntimeError("No active merge request found for the current branch.")
    return merge_request["iid"]


def open_merge_request_in_browser(config: AppConfig, api: GitLabApi) -> None:
    try:
        merge_request_id = get_active_merge_request_id(api)
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = f"{config.base_url}/{remote_url.split(':')[1][:-4]}"
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except (subprocess.CalledProcessError, RuntimeError):
        return
