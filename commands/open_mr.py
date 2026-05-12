import subprocess
import json
import webbrowser
from config import BASE_URL, API_URL, GITLAB_TOKEN, MAIN_BRANCH_DEFAULT
import gitlab_api
import git_utils
from commands.common import get_project_id

def open_mr_in_browser():
    try:
        branch = git_utils.get_current_branch()
        project_id = get_project_id()
        mr = gitlab_api.get_merge_request_for_branch(project_id, branch)
        if not mr:
            print("No active merge request found for current branch.")
            return
            
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = BASE_URL + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{mr['iid']}")
    except Exception as e:
        print(f"Error opening merge request: {e}")
