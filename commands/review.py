import subprocess

from config import API_URL
from gitlab_api import getCurrentIssueId, addReviewersToMergeRequest
from interactive import chooseReviewersManually


def track_issue_time():
    # Get the current merge request
    try:
        project_id = get_project_id()
        issue_id = getCurrentIssueId()
    except Exception as e:
        print(f"Error getting issue details: {str(e)}")
        return

    # Prompt for actual time spent
    spent_time = inquirer.prompt([
        inquirer.Text('spent_time',
                      message='How many minutes did you actually spend on this issue?',
                      validate=lambda _, x: x.isdigit())
    ])['spent_time']

    # Add spent time to the issue description
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

