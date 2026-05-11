from __future__ import annotations

import webbrowser

from githappens.commands.review import get_merge_request_for_current_branch
from githappens.git_utils import build_merge_request_url, get_project_link_from_current_dir


def open_merge_request_in_browser(runtime, client, project_id):
    merge_request = get_merge_request_for_current_branch(client, project_id)
    remote_url = get_project_link_from_current_dir()
    if not remote_url:
        return

    webbrowser.open(build_merge_request_url(runtime.config.base_url, remote_url, merge_request["iid"]))
