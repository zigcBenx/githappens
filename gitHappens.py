#!/usr/bin/env python3
import subprocess
import json
import argparse
import configparser
import inquirer
import datetime
import re
import os
import requests
import sys
import webbrowser

# Setup config parser and read settings
config = configparser.ConfigParser()
absolute_config_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(absolute_config_path, 'configs/config.ini')
config.read(config_path)

BASE_URL        = config.get('DEFAULT', 'base_url')
API_URL         = BASE_URL + '/api/v4'
GROUP_ID        = config.get('DEFAULT', 'group_id')
CUSTOM_TEMPLATE = config.get('DEFAULT', 'custom_template')
GITLAB_TOKEN    = config.get('DEFAULT', 'GITLAB_TOKEN')
DELETE_BRANCH   = config.get('DEFAULT', 'delete_branch_after_merge').lower() == 'true'
DEVELOPER_EMAIL = config.get('DEFAULT', 'developer_email', fallback=None)
SQUASH_COMMITS  = config.get('DEFAULT', 'squash_commits').lower() == 'true'
PRODUCTION_PIPELINE_NAME = config.get('DEFAULT', 'production_pipeline_name', fallback='deploy')
PRODUCTION_JOB_NAME = config.get('DEFAULT', 'production_job_name', fallback=None)
PRODUCTION_REF = config.get('DEFAULT', 'production_ref', fallback=None)
MAIN_BRANCH     = 'master'

# Read templates from json config
with open(os.path.join(absolute_config_path,'configs/templates.json'), 'r') as f:
    jsonConfig = json.load(f)
TEMPLATES = jsonConfig['templates']
REVIEWERS = jsonConfig['reviewers']
PRODUCTION_MAPPINGS = jsonConfig.get('productionMappings', {})

def get_project_id():
    project_link = getProjectLinkFromCurrentDir()
    if (project_link == -1):
        return enterProjectId()

    allProjects = get_all_projects(project_link)
    # Find projects id by project ssh link gathered from repo
    matching_id = None
    for project in allProjects:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id

def get_all_projects(project_link):
    url = API_URL + "/projects?membership=true&search=" + project_link.split('/')[-1].split('.')[0]

    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")

def getProjectLinkFromCurrentDir():
    try:
        cmd = 'git remote get-url origin'
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            output = result.stdout.decode('utf-8').strip()
            return output
        else:
            return -1
    except FileNotFoundError:
        return -1

def enterProjectId():
    while True:
        project_id = input('Please enter the ID of your GitLab project: ')
        if project_id:
            return project_id
        exit('Invalid project ID.')

def list_milestones(current=False):
    cmd = f'glab api /groups/{GROUP_ID}/milestones?state=active'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    milestones = json.loads(result.stdout)
    if current:
        today = datetime.date.today().strftime('%Y-%m-%d')
        active_milestones = []
        for milestone in milestones:
            start_date = milestone['start_date']
            due_date = milestone['due_date']
            if start_date and due_date and start_date <= today and due_date >= today:
                active_milestones.append(milestone)
        active_milestones.sort(key=lambda x: x['due_date'])
        return active_milestones[0]
    return milestones

def select_template():
    template_names = [t['name'] for t in TEMPLATES]
    template_names.append(CUSTOM_TEMPLATE)
    questions = [
        inquirer.List('template',
                      message="Select template:",
                      choices=template_names,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['template']

def getIssueSettings(template_name):
    if template_name == CUSTOM_TEMPLATE:
        return {}
    return next((t for t in TEMPLATES if t['name'] == template_name), None)

def createIssue(title, project_id, milestoneId, epic, iteration, settings):
    if settings:
        issueType = settings.get('type') or 'issue'
        return executeIssueCreate(project_id, title, settings.get('labels'), milestoneId, epic, iteration, settings.get('weight'), settings.get('estimated_time'), issueType)
    print("No settings in template")
    exit(2)
    pass

def executeIssueCreate(project_id, title, labels, milestoneId, epic, iteration, weight, estimated_time, issue_type='issue'):
    labels = ",".join(labels) if type(labels) == list else labels
    assignee_id = getAuthorizedUser()['id']
    issue_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f'title={title}',
        "-f", f'assignee_ids={assignee_id}',
        "-f", f'issue_type={issue_type}'
    ]
    if labels:
        issue_command.append("-f")
        issue_command.append(f'labels={labels}')

    if weight:
        issue_command.append("-f")
        issue_command.append(f'weight={str(weight)}')

    if milestoneId:
        issue_command.append("-f")
        issue_command.append(f'milestone_id={str(milestoneId)}')

    if epic:
        epicId = epic['id']
        issue_command.append("-f")
        issue_command.append(f'epic_id={str(epicId)}')

    # Set the description, including iteration, estimated time, and other info
    description = ""
    if iteration:
        iterationId = iteration['id']
        description += f"/iteration *iteration:{str(iterationId)} "

    if estimated_time:
        description += f"\n/estimate {estimated_time}m "

    issue_command.extend(["-f", f'description={description}'])

    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())

def select_milestone(milestones):
    milestones = [t['title'] for t in milestones]
    questions = [
        inquirer.List('milestones',
                      message="Select milestone:",
                      choices=milestones,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['milestones']

def getSelectedMilestone(milestone, milestones):
    return next((t for t in milestones if t['title'] == milestone), None)

def get_milestone(manual):
    if manual:
        milestones = list_milestones()
        return getSelectedMilestone(select_milestone(milestones), milestones)
    milestone = list_milestones(True) # select active for today
    return milestone

def get_iteration(manual):
    if manual:
        iterations = list_iterations()
        return getSelectedIteration(select_iteration(iterations), iterations)
    return getActiveIteration()

def getSelectedIteration(iteration, iterations):
    return next((t for t in iterations if t['start_date'] + ' - ' + t['due_date'] == iteration), None)

def select_iteration(iterations):
    iterations = [t['start_date'] + ' - ' + t['due_date'] for t in iterations]
    questions = [
        inquirer.List('iterations',
                      message="Select iteration:",
                      choices=iterations,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['iterations']

def list_iterations():
    cmd = f'glab api /groups/{GROUP_ID}/iterations?state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    iterations = json.loads(result.stdout)
    return iterations

def getActiveIteration():
    iterations = list_iterations()
    today = datetime.date.today().strftime('%Y-%m-%d')
    active_iterations = []
    for iteration in iterations:
        start_date = iteration['start_date']
        due_date = iteration['due_date']
        if start_date and due_date and start_date <= today and due_date >= today:
            active_iterations.append(iteration)
    active_iterations.sort(key=lambda x: x['due_date'])
    return active_iterations[0]

def getAuthorizedUser():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)

def list_epics():
    cmd = f'glab api /groups/{GROUP_ID}/epics?per_page=1000&state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)

def select_epic(epics):
    epics = [t['title'] for t in epics]
    search_query = inquirer.prompt([
        inquirer.Text('search_query', message='Search epic:'),
    ])['search_query']

    # Filter choices based on search query
    filtered_epics = [c for c in epics if search_query.lower() in c.lower()]
    questions = [
        inquirer.List('epics',
                      message="Select epic:",
                      choices=filtered_epics,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['epics']

def getSelectedEpic(epic, epics):
    return next((t for t in epics if t['title'] == epic), None)

def get_epic():
    epics = list_epics()
    return getSelectedEpic(select_epic(epics), epics)

def create_branch(project_id, issue):
    issueId = str(issue['iid'])
    title = re.sub('\\s+', '-', issue['title']).lower()
    title = issueId + '-' + title.replace(':','').replace('(',' ').replace(')', '').replace(' ','-')
    branch_output = subprocess.check_output(["glab", "api", f"/projects/{str(project_id)}/repository/branches", "-f", f'branch={title}', "-f", f'ref={MAIN_BRANCH}', "-f", f'issue_iid={issueId}'])
    return json.loads(branch_output.decode())

def create_merge_request(project_id, branch, issue, labels, milestoneId):
    issueId = str(issue['iid'])
    branch = branch['name']
    title = issue['title']
    assignee_id = getAuthorizedUser()['id']
    labels = ",".join(labels) if type(labels) == list else labels
    merge_request_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f", f'title={title}',
        "-f", f'description="Closes #{issueId}"',
        "-f", f'source_branch={branch}',
        "-f", f'target_branch={MAIN_BRANCH}',
        "-f", f'issue_iid={issueId}',
        "-f", f'assignee_ids={assignee_id}'
    ]

    if SQUASH_COMMITS:
        merge_request_command.append("-f")
        merge_request_command.append("squash=true")

    if DELETE_BRANCH:
        merge_request_command.append("-f")
        merge_request_command.append("remove_source_branch=true")

    if labels:
        merge_request_command.append("-f")
        merge_request_command.append(f'labels={labels}')

    if milestoneId:
        merge_request_command.append("-f")
        merge_request_command.append(f'milestone_id={str(milestoneId)}')

    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())

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

    createdBranch = create_branch(project_id, createdIssue)

    createdMergeRequest = create_merge_request(project_id, createdBranch, createdIssue, selectedSettings.get('labels'), milestone)
    print(f"Merge request #{createdMergeRequest['iid']}: {createdMergeRequest['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{createdMergeRequest['source_branch']}' 'origin/{createdMergeRequest['source_branch']}'")
    print("to switch to new branch.")

    return createdIssue

def getCurrentBranch():
    return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()

def openMergeRequestInBrowser():
    try:
        merge_request_id = getActiveMergeRequestId()
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = BASE_URL + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None

def getActiveMergeRequestId():
    branch_to_find = getCurrentBranch()
    return find_merge_request_id_by_branch(branch_to_find)

def find_merge_request_id_by_branch(branch_name):
    return getMergeRequestForBranch(branch_name)['iid']

def getMergeRequestForBranch(branchName):
    project_id = get_project_id()
    api_url = f"{API_URL}/projects/{project_id}/merge_requests"
    headers = {"Private-Token": GITLAB_TOKEN}

    params = {
        "source_branch": branchName,
    }

    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        merge_requests = response.json()
        for mr in merge_requests:
            if mr["source_branch"] == branchName:
                return mr
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None

def chooseReviewersManually():
    """Prompt the user to select reviewers manually from the available list, showing names."""
    # Fetch user details for each reviewer ID
    reviewer_choices = []
    for reviewer_id in REVIEWERS:
        api_url = f"{API_URL}/users/{reviewer_id}"
        headers = {"Private-Token": GITLAB_TOKEN}
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                user = response.json()
                display_name = f"{user.get('name')} ({user.get('username')})"
                reviewer_choices.append((display_name, reviewer_id))
            else:
                reviewer_choices.append((str(reviewer_id), reviewer_id))
        except Exception:
            reviewer_choices.append((str(reviewer_id), reviewer_id))

    questions = [
        inquirer.Checkbox(
            "selected_reviewers",
            message="Select reviewers",
            choices=[(name, str(rid)) for name, rid in reviewer_choices],
        )
    ]
    answers = inquirer.prompt(questions)
    if answers and "selected_reviewers" in answers:
        return [int(r) for r in answers["selected_reviewers"]]
    else:
        return []

def addReviewersToMergeRequest(reviewers=None):
    project_id = get_project_id()
    mr_id = getActiveMergeRequestId()
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": GITLAB_TOKEN}

    data = {
        "reviewer_ids": reviewers if reviewers is not None else REVIEWERS
    }

    requests.put(api_url, headers=headers, json=data)

def setMergeRequestToAutoMerge():
    project_id = get_project_id()
    mr_id = getActiveMergeRequestId()
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}/merge"
    headers = {"Private-Token": GITLAB_TOKEN}

    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }

    requests.put(api_url, headers=headers, json=data)

def getMainBranch():
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    return output.strip()


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime('%Y-%m-%d')

    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if (DEVELOPER_EMAIL):
        cmd = f'{cmd} | grep {DEVELOPER_EMAIL}'
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
    openai_api_key = config.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
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
        incident_project_id = config.get('DEFAULT', 'incident_project_id')
    except (configparser.NoOptionError, configparser.NoSectionError):
        print("Error: incident_project_id not found in config.ini")
        print("Please add your incident project ID to configs/config.ini under [DEFAULT] section:")
        print("incident_project_id = your_project_id_here")
        return

    issue_title = f"Incident Report: {text}"

    selected_label = selectLabels('Department')

    incident_settings = {
        'labels': ['incident', 'report'],
        'onlyIssue': True,
        'type': 'incident'
    }

    if selected_label:
        incident_settings['labels'].append(selected_label)

    try:
        # Create the incident issue
        iteration = getActiveIteration()
        created_issue = createIssue(issue_title, incident_project_id, False, False, iteration, incident_settings)
        issue_iid = created_issue['iid']

        closeOpenedIssue(issue_iid, incident_project_id)
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

def closeOpenedIssue(issue_iid, project_id):
    issue_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        '-X', 'PUT',
        '-f', 'state_event=close'
    ]
    try:
        subprocess.run(issue_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {str(e)}")

def selectLabels(search, multiple = False):
    labels = getLabelsOfGroup(search)
    labels = sorted([t['name'] for t in labels])
    
    question_type = inquirer.Checkbox if multiple else inquirer.List
    questions = [
        question_type(
            'labels',
            message="Select one or more department labels:",
            choices=labels,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer['labels']

def getLabelsOfGroup(search=''):
    cmd = f'glab api /groups/{GROUP_ID}/labels?search={search}'
    try:
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []

def getCurrentIssueId():
    mr = getMergeRequestForBranch(getCurrentBranch())
    return mr['description'].replace('"','').replace('#','').split()[1]

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

def get_last_production_deploy():
    try:
        project_id = get_project_id()
        api_url = f"{API_URL}/projects/{project_id}/pipelines"
        headers = {"Private-Token": GITLAB_TOKEN}

        # Set up parameters for the pipeline search
        params = {
            "per_page": 50,
            "order_by": "updated_at",
            "sort": "desc"
        }

        # Add ref filter if specified in config
        if PRODUCTION_REF:
            params["ref"] = PRODUCTION_REF
        else:
            # Use main branch if no specific ref is configured
            try:
                main_branch = getMainBranch()
                params["ref"] = main_branch
            except:
                # Fallback to common main branch names
                params["ref"] = "main"

        response = requests.get(api_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
            return

        pipelines = response.json()
        production_pipeline = None

        # Look for production pipeline by name pattern
        for pipeline in pipelines:
            # Get pipeline details to check jobs
            pipeline_detail_url = f"{API_URL}/projects/{project_id}/pipelines/{pipeline['id']}/jobs"
            detail_response = requests.get(pipeline_detail_url, headers=headers)

            if detail_response.status_code == 200:
                jobs = detail_response.json()

                # Check if this pipeline contains production deployment
                for job in jobs:
                    job_name = job.get('name', '')
                    stage = job.get('stage', '')
                    job_status = job.get('status', '').lower()

                    # Only consider successful jobs
                    if job_status != 'success':
                        continue

                    # Check project-specific mapping first
                    project_mapping = PRODUCTION_MAPPINGS.get(str(project_id))
                    if project_mapping:
                        expected_stage = project_mapping.get('stage', '').lower()
                        expected_job = project_mapping.get('job', '').lower()

                        if (stage.lower() == expected_stage or
                            (expected_job and job_name.lower() == expected_job)):
                            production_pipeline = {
                                'pipeline': pipeline,
                                'production_job': job
                            }
                            break
                    else:
                        print('Didn\'t find deployment pipeline')

                if production_pipeline:
                    break

        if not production_pipeline:
            print(f"No production deployment found matching pattern '{PRODUCTION_PIPELINE_NAME}'")
            print("Consider updating the 'production_pipeline_name' setting in your config.ini")
            return

        # Display the results
        pipeline = production_pipeline['pipeline']
        job = production_pipeline['production_job']

        print(f"🚀 Last Production Deployment:")
        print(f"   Pipeline: #{pipeline['id']} - {pipeline['status']}")
        print(f"   Job: {job['name']} ({job['status']})")
        print(f"   Branch/Tag: {pipeline['ref']}")
        print(f"   Started: {job.get('started_at', 'N/A')}")
        print(f"   Finished: {job.get('finished_at', 'N/A')}")
        print(f"   Duration: {job.get('duration', 'N/A')} seconds" if job.get('duration') else "   Duration: N/A")
        print(f"   Commit: {pipeline['sha'][:8]}")
        print(f"   URL: {pipeline['web_url']}")

        # Show time since deployment
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
            except:
                pass

    except Exception as e:
        print(f"Error fetching last production deploy: {str(e)}")

def main():
    global MAIN_BRANCH

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
        track_issue_time()
        reviewers = None
        if getattr(args, "select", False):
            reviewers = chooseReviewersManually()
        addReviewersToMergeRequest(reviewers=reviewers)
        if(args.auto_merge):
            setMergeRequestToAutoMerge()
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

    # Get settings for issue from template
    selectedSettings = getIssueSettings(select_template())

    # If template is False, ask for each settings
    if not len(selectedSettings):
        print('Custom selection of issue settings is not supported yet')
        pass

    if args.project_id and selectedSettings.get('projectIds'):
        print('NOTE: Overwriting project id from argument...')

    project_id = selectedSettings.get('projectIds') or args.project_id or get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = get_milestone(args.milestone)['id']

    iteration = False
    if not args.no_iteration:
        # manual pick iteration
        iteration = get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = get_epic()

    MAIN_BRANCH = getMainBranch()

    onlyIssue = selectedSettings.get('onlyIssue') or args.only_issue

    if type(project_id) == list:
        for id in project_id:
            startIssueCreation(id, title, milestone, epic, iteration, selectedSettings, onlyIssue)
    else:
        startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue)

if __name__ == '__main__':
    main()