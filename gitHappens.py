#!/usr/bin/env python3
import subprocess
import argparse
import configparser
import config
import gitlab_api
import git_utils
import templates
import interactive
import inquirer
import datetime
import sys
import webbrowser

def createIssue(title, project_id, milestoneId, epic, iteration, settings):
    if settings:
        issueType = settings.get('type') or 'issue'
        return gitlab_api.executeIssueCreate(project_id, title, settings.get('labels'), milestoneId, epic, iteration, settings.get('weight'), settings.get('estimated_time'), issueType)
    print("No settings in template")
    exit(2)
    pass

def startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue):
    # Prompt for estimated time
    estimated_time = inquirer.prompt([
        inquirer.Text('estimated_time',
                      message='Estimated time to complete this issue (in minutes, optional)',
                      validate=lambda _, x: x == '' or x.isdigit())
    ])['estimated_time']

    # If multiple project IDs, split the estimated time
    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time

    # Modify settings to include estimated time
    if estimated_time_per_project:
        selectedSettings = selectedSettings.copy() if selectedSettings else {}
        selectedSettings['estimated_time'] = int(estimated_time_per_project)

    createdIssue = createIssue(title, project_id, milestone, epic, iteration, selectedSettings)
    print(f"Issue #{createdIssue['iid']}: {createdIssue['title']} created.")

    if onlyIssue:
        return createdIssue

    createdBranch = gitlab_api.create_branch(project_id, createdIssue)

    createdMergeRequest = gitlab_api.create_merge_request(project_id, createdBranch, createdIssue, selectedSettings.get('labels'), milestone)
    print(f"Merge request #{createdMergeRequest['iid']}: {createdMergeRequest['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{createdMergeRequest['source_branch']}' 'origin/{createdMergeRequest['source_branch']}'")
    print("to switch to new branch.")

    return createdIssue

def openMergeRequestInBrowser():
    try:
        merge_request_id = interactive.getActiveMergeRequestId()
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = config.BASE_URL + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None

def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime('%Y-%m-%d')

    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if (config.DEVELOPER_EMAIL):
        cmd = f'{cmd} | grep {config.DEVELOPER_EMAIL}'
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

    # Check if OpenAI API key is set
    openai_api_key = config.ini.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
    if not openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    # Dynamically import openai only if API key is present
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
    # Get the incident project ID from config
    try:
        incident_project_id = config.ini.get('DEFAULT', 'incident_project_id')
    except (configparser.NoOptionError, configparser.NoSectionError):
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"

    selected_label = interactive.selectLabels('Department')

    incident_settings = {
        'labels': ['incident', 'report'],
        'onlyIssue': True,
        'type': 'incident'
    }

    if selected_label:
        incident_settings['labels'].append(selected_label)

    try:
        # Create the incident issue
        iteration = gitlab_api.getActiveIteration()
        created_issue = createIssue(issue_title, incident_project_id, False, False, iteration, incident_settings)
        issue_iid = created_issue['iid']

        gitlab_api.closeOpenedIssue(issue_iid, incident_project_id)
        print(f"Incident issue #{issue_iid} created successfully.")
        print(f"Title: {issue_title}")

        # Add time tracking to the issue
        time_tracking_command = [
            "glab", "api",
            f"/projects/{incident_project_id}/issues/{issue_iid}/add_spent_time",
            "-f", f"duration={minutes}m"
        ]

        try:
            subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Added {minutes} minutes to issue time tracking.")
        except subprocess.CalledProcessError as e:
            print(f"Error adding time tracking: {str(e)}")

    except Exception as e:
        print(f"Error creating incident issue: {str(e)}")

def get_last_production_deploy():
    try:
        project_id = interactive.get_project_id()
        if config.MAIN_BRANCH:
            pipeline_ref = config.MAIN_BRANCH
        else:
            try:
                pipeline_ref = git_utils.getMainBranch()
            except Exception:
                pipeline_ref = "main"

        result = gitlab_api.get_last_production_deploy_info(project_id, ref=pipeline_ref)
        if result.get('error') == 'pipelines_fetch':
            print(f"Failed to fetch pipelines: {result['status']} - {result['text']}")
            return
        if result.get('error') == 'not_found':
            print(f"No production deployment found matching pattern")
            return

        pipeline = result['pipeline']
        job = result['production_job']

        print(f"🚀 Last Production Deployment:")
        print(f"   Pipeline: #{pipeline['id']} - {pipeline['status']}")
        print(f"   Job: {job['name']} ({job['status']})")
        print(f"   Branch/Tag: {pipeline['ref']}")
        print(f"   Started: {job.get('started_at', 'N/A')}")
        print(f"   Finished: {job.get('finished_at', 'N/A')}")
        print(f"   Duration: {job.get('duration', 'N/A')} seconds" if job.get('duration') else "   Duration: N/A")
        print(f"   Commit: {pipeline['sha'][:8]}")
        print(f"   URL: {pipeline['web_url']}")

        if job.get('finished_at'):
            try:
                finished_time = datetime.datetime.fromisoformat(job['finished_at'].replace('Z', '+00:00'))
                time_diff = datetime.datetime.now(datetime.timezone.utc) - finished_time

                if time_diff.days > 0:
                    print(f"   ⏰ {time_diff.days} days ago")
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    print(f"   ⏰ {hours} hours ago")
                else:
                    minutes = time_diff.seconds // 60
                    print(f"   ⏰ {minutes} minutes ago")
            except Exception:
                pass

    except Exception as e:
        print(f"Error fetching last production deploy: {str(e)}")

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

    # If no arguments passed, show help
    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)

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
            print("Invalid minutes. Please provide a valid number.")
        return

    # So it takes all text until first known argument
    title = " ".join(args.title)

    if title == 'open':
        openMergeRequestInBrowser()
        return
    elif title == 'review':
        interactive.track_issue_time()
        project_id = interactive.get_project_id()
        mr_id = interactive.getActiveMergeRequestId()
        reviewers = None
        if getattr(args, "select", False):
            reviewers = interactive.chooseReviewersManually()
        gitlab_api.addReviewersToMergeRequest(project_id, mr_id, reviewers=reviewers)

        try:
            from ai_code_review import run_review_for_mr
            run_review_for_mr(project_id, mr_id, config.GITLAB_TOKEN, config.API_URL)
        except Exception as e:
            print(f"AI review skipped: {e}")

        if args.auto_merge:
            gitlab_api.setMergeRequestToAutoMerge(project_id, mr_id)
        return
    elif title == 'summary':
        get_two_weeks_commits()
        return
    elif title == 'summaryAI':
        generate_smart_summary()
        return
    elif title == 'last deploy':
        get_last_production_deploy()
        return
    elif title == 'ai review':
        from ai_code_review import run_review
        run_review()
        return

    # Get settings for issue from template
    selectedSettings = templates.getIssueSettings(templates.select_template())

    # If template is False, ask for each settings
    if not len(selectedSettings):
        print('Custom selection of issue settings is not supported yet')
        pass

    if args.project_id and selectedSettings.get('projectIds'):
        print('NOTE: Overwriting project id from argument...')

    project_id = selectedSettings.get('projectIds') or args.project_id or interactive.get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = interactive.get_milestone(args.milestone)['id']

    iteration = False
    if not args.no_iteration:
        # manual pick iteration
        iteration = interactive.get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = interactive.get_epic()

    config.set_main_branch(git_utils.getMainBranch())

    onlyIssue = selectedSettings.get('onlyIssue') or args.only_issue

    if type(project_id) == list:
        for id in project_id:
            startIssueCreation(id, title, milestone, epic, iteration, selectedSettings, onlyIssue)
    else:
        startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue)

if __name__ == '__main__':
    main()