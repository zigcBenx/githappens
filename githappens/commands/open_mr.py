import subprocess
import webbrowser

from .. import git_utils, gitlab_api


def get_active_merge_request_id(ctx):
    branch_to_find = git_utils.get_current_branch()
    return gitlab_api.find_merge_request_id_by_branch(ctx, branch_to_find)


def open_merge_request_in_browser(ctx):
    try:
        merge_request_id = get_active_merge_request_id(ctx)
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
        url = ctx.settings.base_url + "/" + remote_url.split(":")[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except (subprocess.CalledProcessError, TypeError, IndexError):
        return None
