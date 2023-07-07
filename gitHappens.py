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

# Setup config parser and read settings
config = configparser.ConfigParser()
absolute_config_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(absolute_config_path, 'configs/config.ini')
config.read(config_path)
GROUP_ID=config.get('DEFAULT', 'group_id')
CUSTOM_TEMPLATE=config.get('DEFAULT', 'custom_template')
GITLAB_TOKEN=config.get('DEFAULT', 'GITLAB_TOKEN')

# Read templates from json config
with open(os.path.join(absolute_config_path,'configs/templates.json'), 'r') as f:
    jsonConfig = json.load(f)
TEMPLATES = jsonConfig['templates']

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
    url = "https://gitlab.com/api/v4/projects?membership=true&search=" + project_link.split('/')[-1].split('.')[0]

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
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        return output.strip()
    except StopIteration:
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
            if start_date <= today and due_date >= today:
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
        return []
    return next((t for t in TEMPLATES if t['name'] == template_name), None)

def createIssue(title, project_id, milestoneId, epic, settings):
    if settings:
        # if project is set in template use that
        project_id = settings['project_id'] if 'project_id' in settings else project_id
        name, weight, labels = settings.values()
        return executeIssueCreate(project_id, title, labels, milestoneId, epic, weight)
        
    
    # TODO: ask for each one
    print("no settings")
    pass

def executeIssueCreate(project_id, title, labels, milestoneId, epic, weight):
    labels = ",".join(labels)
    assignee_id = getAuthorizedUser()['id']
    issue_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f'title={title}',
        "-f", f'labels={labels}',
        "-f", f'milestone_id={str(milestoneId)}',
        "-f", f'weight={str(weight)}',
        "-f", f'assignee_ids={assignee_id}',
    ]

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
    milestone = list_milestones(True)
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
    branch_output = subprocess.check_output(["glab", "api", f"/projects/{str(project_id)}/repository/branches", "-f", f'branch={title}', "-f", 'ref=master', "-f", f'issue_iid={issueId}'])
    return json.loads(branch_output.decode())

def create_merge_request(project_id, branch, issue):
    issueId = str(issue['iid'])
    branch = branch['name']
    title = issue['title']
    mr_output = subprocess.check_output(["glab", "api", f"/projects/{str(project_id)}/merge_requests", "-f", f'title={title}', "-f", f'description="Closes #{issueId}"', "-f", f'source_branch={branch}', "-f", 'target_branch=master', "-f", 'remove_source_branch=true', "-f", f'issue_iid={issueId}'])
    return json.loads(mr_output.decode())

def main():
    parser = argparse.ArgumentParser("Argument desciprition of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument(f"--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument("-m", "--milestone", action='store_true', help="Add this flag, if you want to manualy select milestone")
    parser.add_argument("--no_epic", action="store_true", help="Add this flag if you don't want to pick epic")

    args = parser.parse_args()

    # So it takes all text until first known argument
    title = " ".join(args.title)
    
    project_id = args.project_id or get_project_id()

    milestone = get_milestone(args.milestone)

    selectedSettings = getIssueSettings(select_template())

    epic = False
    if not args.no_epic:
        epic = get_epic()

    createdIssue = createIssue(title, project_id, milestone['id'], epic, selectedSettings)
    print(f"Issue #{createdIssue['iid']}: {createdIssue['title']} created.")

    createdBranch = create_branch(project_id, createdIssue)

    createdMergeRequest = create_merge_request(project_id, createdBranch, createdIssue)
    print(f"Merge request #{createdMergeRequest['iid']}: {createdMergeRequest['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{createdMergeRequest['source_branch']}' 'origin/{createdMergeRequest['source_branch']}'")
    print("to switch to new branch.")



if __name__ == '__main__':
    main()
