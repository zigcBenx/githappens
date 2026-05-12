import argparse
import sys
import os
from config import GITLAB_TOKEN, API_URL, DEVELOPER_EMAIL
import git_utils
import interactive
import templates
from commands.common import get_project_id, get_milestone, get_iteration, get_epic
from commands.create_issue import start_issue_creation
from commands.review import review_workflow
from commands.deploy import check_last_production_deploy
from commands.open_mr import open_mr_in_browser

def generate_smart_summary():
    commits = git_utils.get_two_weeks_commits(return_output=True)
    if not commits:
        return
    
    import config
    openai_api_key = config.config.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
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
    import config
    try:
        incident_project_id = config.config.get('DEFAULT', 'incident_project_id')
    except:
        print("Error: incident_project_id not found in config.ini")
        return
    
    issue_title = f"Incident Report: {text}"
    
    # We need a list of labels for the group
    import subprocess
    import json
    from config import GROUP_ID
    cmd = f'glab api /groups/{GROUP_ID}/labels?search=Department'
    labels_data = json.loads(subprocess.check_output(cmd.split()).decode())
    labels = sorted([t['name'] for t in labels_data])
    
    selected_label = interactive.select_labels(labels)
    
    incident_settings = {
        'labels': ['incident', 'report'],
        'onlyIssue': True,
        'type': 'incident'
    }
    if selected_label:
        incident_settings['labels'].append(selected_label)
    
    # Create issue
    from commands.create_issue import execute_issue_create
    iteration = get_iteration(False)
    created_issue = execute_issue_create(
        incident_project_id, 
        issue_title, 
        incident_settings['labels'], 
        False, 
        False, 
        iteration, 
        incident_settings.get('weight'), 
        incident_settings.get('estimated_time'), 
        incident_settings['type']
    )
    
    # Close it immediately as per original code
    import subprocess
    issue_iid = created_issue['iid']
    close_command = ["glab", "api", f"/projects/{incident_project_id}/issues/{issue_iid}", "-X", "PUT", "-f", "state_event=close"]
    subprocess.run(close_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    print(f"Incident issue #{issue_iid} created successfully.")
    
    # Add time tracking
    time_command = ["glab", "api", f"/projects/{incident_project_id}/issues/{issue_iid}/add_spent_time", "-f", f"duration={minutes}m"]
    subprocess.run(time_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"Added {minutes} minutes to issue time tracking.")

def main():
    parser = argparse.ArgumentParser("Argument description of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument(f"--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument("-m", "--milestone", action='store_true', help="Add this flag, if you want to manually select milestone")
    parser.add_argument("--no_epic", action="store_true", help="Add this flag if you don't want to pick epic")
    parser.add_argument("--no_milestone", action="store_true", help="Add this flag if you don't want to pick milestone")
    parser.add_argument("--no_iteration", action="store_true", help="Add this flag if you don't want to pick iteration")
    parser.add_argument("--only_issue", action="store_true", help="Add this flag if you don't want to create merge request and branch alongside issue")
    parser.add_argument("-am", "--auto_merge", action="store_true", help="Add this flag to review if you want to set merge request to auto merge when pipeline succeeds")
    parser.add_argument("--select", action="store_true", help="Manually select reviewers for merge request (interactive)")

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    
    if args.title[0] == 'report':
        parts = args.title
        if len(parts) != 3:
            print("Invalid report format. Use: gh report \"text\" minutes")
            return
        text = parts[1]
        try:
            minutes = int(parts[2].strip())
            process_report(text, minutes)
        except ValueError:
            print("Invalid minutes. Please provide a valid number")
        return

    title = " ".join(args.title)
    if title == 'open':
        open_mr_in_browser()
        return
    elif title == 'review':
        review_workflow(select_reviewers=args.select, auto_merge=args.auto_merge)
        return
    elif title == 'summary':
        git_utils.get_two_weeks_commits(developer_email=DEVELOPER_EMAIL)
        return
    elif title == 'summaryAI':
        generate_smart_summary()
        return
    elif title == 'last deploy':
        check_last_production_deploy()
        return
    elif title == 'ai review':
        import subprocess
        # Original code did: from ai_code_review import run_review; run_review()
        try:
            from ai_code_review import run_review
            run_review()
        except ImportError:
            print("ai_code_review module not found.")
        return

    # Issue creation flow
    from config import TEMPLATES
    selected_template_name = interactive.select_template(TEMPLATES)
    selected_settings = templates.get_issue_settings(selected_template_name)
    
    if not selected_settings:
        print('Custom selection of issue settings is not supported yet')
        # In a real scenario we'd handle this or just a return
    
    project_id = selected_settings.get('projectIds') if selected_settings else None
    if project_id and args.project_id:
        print('NOTE: Overwriting project id from argument...')
    
    project_id = project_id or args.project_id or get_project_id()
    
    milestone_id = None
    if not args.no_milestone:
        milestone = get_milestone(args.milestone)
        milestone_id = milestone['id'] if milestone else None
    
    iteration = None
    if not args.no_iteration:
        iteration = get_iteration(True)
    
    epic = None
    if not args.no_epic:
        epic = get_epic()
    
    # Use the current branch as default for MRs
    current_main = git_utils.get_main_branch()
    
    only_issue = selected_settings.get('onlyIssue') if selected_settings else False
    only_issue = only_issue or args.only_issue
    
    if isinstance(project_id, list):
        for pid in project_id:
            start_issue_creation(pid, title, milestone_id, epic, iteration, selected_settings, only_issue)
    else:
        start_issue_creation(project_id, title, milestone_id, epic, iteration, selected_settings, only_issue)

if __name__ == '__main__':
    main()
