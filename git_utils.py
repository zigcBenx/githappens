"""Git operations: commit history, AI summaries, incident reporting."""
import subprocess
import datetime
from config import get_developer_email, get_openai_api_key, get_incident_project_id
from gitlab_api import getActiveIteration, closeOpenedIssue, getMergeRequestForBranch, getCurrentBranch
from templates import selectLabels


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime('%Y-%m-%d')
    dev_email = get_developer_email()
    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if dev_email:
        cmd += f' | grep {dev_email}'
    try:
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, universal_newlines=True).strip()
        if output:
            if return_output:
                return output
            print(output)
        else:
            print("No commits found.")
            return "" if return_output else None
    except subprocess.CalledProcessError as e:
        print(f"No commits were found or an error occurred. (exit status {e.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None


def generate_smart_summary():
    commits = get_two_weeks_commits(return_output=True)
    if not commits:
        return
    openai_api_key = get_openai_api_key()
    if not openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return
    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Please install it using: pip install openai")
        return
    openai.api_key = openai_api_key
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes git commits. Provide a concise, well-organized summary of the main changes and themes."},
                {"role": "user", "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}"}
            ]
        )
        print("\n📋 AI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating AI summary: {e}")


def process_report(text, minutes):
    incident_project_id = get_incident_project_id()
    selected_label = selectLabels('Department')
    incident_settings = {
        'labels': ['incident', 'report'],
        'onlyIssue': True,
        'type': 'incident'
    }
    if selected_label:
        incident_settings['labels'].append(selected_label)
    try:
        iteration = getActiveIteration()
        from gitlab_api import createIssue
        created_issue = createIssue(
            f"Incident Report: {text}", incident_project_id, False, False, iteration, incident_settings
        )
        closeOpenedIssue(created_issue['iid'], incident_project_id)
        print(f"Incident issue #{created_issue['iid']} created successfully.")
        subprocess.run(
            ["glab", "api", f"/projects/{incident_project_id}/issues/{created_issue['iid']}/add_spent_time",
             "-f", f"duration={minutes}m"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(f"Added {minutes} minutes to issue time tracking.")
    except Exception as e:
        print(f"Error creating incident issue: {str(e)}")


def track_issue_time():
    try:
        from config import get_project_id
        project_id = get_project_id()
        mr = getMergeRequestForBranch(getCurrentBranch())
        issue_id = mr['description'].replace('"','').replace('#','').split()[1]
    except Exception as e:
        print(f"Error getting issue details: {str(e)}")
        return
    import inquirer
    spent_time = inquirer.prompt([
        inquirer.Text('spent_time',
                      message='How many minutes did you actually spend on this issue?',
                      validate=lambda _, x: x.isdigit())
    ])['spent_time']
    subprocess.run(
        ["glab", "api", f"/projects/{project_id}/issues/{issue_id}/notes",
         "-f", f"body=/spend {spent_time}m"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )
    print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")