import subprocess
import inquirer

from gitlab_api import (
    get_project_id, get_active_merge_request_id, add_reviewers_to_merge_request,
    set_merge_request_to_auto_merge, get_current_issue_id
)
from interactive import choose_reviewers_manually
from config import get_config


def track_issue_time():
    # Get the current merge request
    try:
        project_id = get_project_id()
        issue_id = get_current_issue_id()
    except Exception as e:
        print(f"Error getting issue details: {str(e)}")
        return
    
    spent_time = inquirer.prompt([
        inquirer.Text('spent_time',
                      message='How many minutes did you actually spend on this issue?',
                      validate=lambda _, x: x.isdigit())
    ])['spent_time']
    
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
    except Exception as e:
        print(f"Error tracking issue time: {str(e)}")


def handle_review_command(args):
    track_issue_time()
    reviewers = None
    if getattr(args, "select", False):
        reviewers = choose_reviewers_manually()
    add_reviewers_to_merge_request(reviewers=reviewers)
    
    # Run AI code review and post to MR
    try:
        from ai_code_review import run_review_for_mr
        config = get_config()
        project_id = get_project_id()
        mr_id = get_active_merge_request_id()
        run_review_for_mr(project_id, mr_id, config.GITLAB_TOKEN, config.API_URL)
    except Exception as e:
        print(f"AI review skipped: {e}")
    
    if args.auto_merge:
        set_merge_request_to_auto_merge()

