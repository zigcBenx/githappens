import subprocess
import json
from config import API_URL, GITLAB_TOKEN, REVIEWERS, PRODUCTION_MAPPINGS
import gitlab_api
import interactive
import git_utils
from commands.common import get_project_id

def get_active_mr_id():
    branch = git_utils.get_current_branch()
    project_id = get_project_id()
    mr = gitlab_api.get_merge_request_for_branch(project_id, branch)
    if mr:
        return mr['iid']
    return None

def review_workflow(select_reviewers=False, auto_merge=False):
    # Track issue time
    track_issue_time()
    
    reviewers = None
    if select_reviewers:
        reviewer_choices = []
        for rid in REVIEWERS:
            user = gitlab_api.get_user_details(rid)
            if user:
                reviewer_choices.append((f"{user.get('name')} ({user.get('username')})", rid))
            else:
                reviewer_choices.append((str(rid), rid))
        reviewers = interactive.prompt_reviewers(reviewer_choices)
    
    project_id = get_project_id()
    mr_id = get_active_mr_id()
    if not mr_id:
        print("No active merge request found for current branch.")
        return

    gitlab_api.update_merge_request_reviewers(project_id, mr_id, reviewers if reviewers is not None else REVIEWERS)
    
    # AI Code Review
    try:
        from ai_code_review import run_review_for_mr
        run_review_for_mr(project_id, mr_id, GITLAB_TOKEN, API_URL)
    except Exception as e:
        print(f"AI review skipped: {e}")
        
    if auto_merge:
        gitlab_api.set_mr_auto_merge(project_id, mr_id)

def track_issue_time():
    project_id = get_project_id()
    branch = git_utils.get_current_branch()
    mr = gitlab_api.get_merge_request_for_branch(project_id, branch)
    if not mr:
        print("Error getting merge request details")
        return
    
    # Original code extracted issue id from description
    issue_id = mr['description'].replace('"','').replace('#','').split()[1]
    
    spent_time = interactive.prompt_spent_time()
    
    # Using glab for time tracking as in original
    time_tracking_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_id}/notes",
        "-f", f"body=/spend {spent_time}m"
    ]
    try:
        subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except subprocess.CalledProcessError as e:
        print(f"Error adding time tracking: {str(e)}")
