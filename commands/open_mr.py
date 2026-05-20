"""Merge request operations."""
from gitlab_api import (
    getCurrentBranch, getActiveMergeRequestId, find_merge_request_id_by_branch,
    getMergeRequestForBranch, getCurrentIssueId,
)
import subprocess
from config import get_base_url

def openMergeRequestInBrowser():
    import webbrowser
    try:
        mr_id = getActiveMergeRequestId()
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
        url = get_base_url() + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{mr_id}")
    except subprocess.CalledProcessError:
        return None

__all__ = [
    'getCurrentBranch', 'getActiveMergeRequestId', 'find_merge_request_id_by_branch',
    'getMergeRequestForBranch', 'getCurrentIssueId', 'openMergeRequestInBrowser',
]