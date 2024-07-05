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
SQUASH_COMMITS  = config.get('DEFAULT', 'squash_commits').lower() == 'true'
MAIN_BRANCH     = 'master'

# Read templates from json config
with open(os.path.join(absolute_config_path,'configs/templates.json'), 'r') as f:
    jsonConfig = json.load(f)
TEMPLATES = jsonConfig['templates']
REVIEWERS = jsonConfig['reviewers']

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

def createIssue(title, project_id, milestoneId, epic, settings):
    if settings:
        return executeIssueCreate(project_id, title, settings.get('labels'), milestoneId, epic, settings.get('weight'))
    print("No settings in template")
    exit(2)
    pass

def executeIssueCreate(project_id, title, labels, milestoneId, epic, weight):
    labels = ",".join(labels) if type(labels) == list else labels
    assignee_id = getAuthorizedUser()['id']
    issue_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f'title={title}',
        "-f", f'assignee_ids={assignee_id}',
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
    title = re.sub('\s+', '-', issue['title']).lower()
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

def startIssueCreation(project_id, title, milestone, epic, selectedSettings, onlyIssue):
    createdIssue = createIssue(title, project_id, milestone, epic, selectedSettings)
    print(f"Issue #{createdIssue['iid']}: {createdIssue['title']} created.")

    if onlyIssue:
        return

    createdBranch = create_branch(project_id, createdIssue)

    createdMergeRequest = create_merge_request(project_id, createdBranch, createdIssue, selectedSettings.get('labels'), milestone)
    print(f"Merge request #{createdMergeRequest['iid']}: {createdMergeRequest['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{createdMergeRequest['source_branch']}' 'origin/{createdMergeRequest['source_branch']}'")
    print("to switch to new branch.")
    return createdMergeRequest['source_branch']

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
    project_id = get_project_id()
    api_url = f"{API_URL}/projects/{project_id}/merge_requests"
    headers = {"Private-Token": GITLAB_TOKEN}

    params = {
        "source_branch": branch_name,
    }

    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        merge_requests = response.json()
        for mr in merge_requests:
            if mr["source_branch"] == branch_name:
                return mr["iid"]
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None

def addReviewersToMergeRequest():
    project_id = get_project_id()
    mr_id = getActiveMergeRequestId()
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": GITLAB_TOKEN}

    data = {
        "reviewer_ids": REVIEWERS
    }

    requests.put(api_url, headers=headers, json=data)

def getMainBranch():
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    return output.strip()

def runGitCommand(command):
    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {command}: {e.stderr.strip()}")
        return None

def hasUncommittedChanges():
    status = runGitCommand(["git", "status", "--porcelain"])
    return status != ""

def main():
    global MAIN_BRANCH

    parser = argparse.ArgumentParser("Argument desciprition of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument(f"--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument("-m", "--milestone", action='store_true', help="Add this flag, if you want to manualy select milestone")
    parser.add_argument("--no_epic", action="store_true", help="Add this flag if you don't want to pick epic")
    parser.add_argument("--no_milestone", action="store_true", help="Add this flag if you don't want to pick milestone")
    parser.add_argument("--only_issue", action="store_true", help="Add this flag if you don't want to create merge request and branch alongside issue")
    parser.add_argument("--auto_switch", action="store_true", help="Auto fetch and switch to new branch")

    # If no arguments passed, show help
    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args()

    # So it takes all text until first known argument
    title = " ".join(args.title)

    if title == 'open':
        openMergeRequestInBrowser()
        return
    elif title == 'review':
        addReviewersToMergeRequest()
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

    epic = False
    if not args.no_epic:
        epic = get_epic()

    MAIN_BRANCH = getMainBranch()

    onlyIssue = selectedSettings.get('onlyIssue') or args.only_issue

    sourceBranch = None
    if type(project_id) == list:
        for id in project_id:
            startIssueCreation(id, title, milestone, epic, selectedSettings, onlyIssue)
    else:
        sourceBranch = startIssueCreation(project_id, title, milestone, epic, selectedSettings, onlyIssue)


    if args.auto_switch and hasUncommittedChanges and sourceBranch:
        print("You have uncommitted changes. Cannot switch to new branch.")
        return

    if args.auto_switch and sourceBranch :
        runGitCommand(["git", "fetch", "origin"])
        runGitCommand(["git", "checkout", "-b", sourceBranch, f"origin/{sourceBranch}"])

if __name__ == '__main__':
    main()
