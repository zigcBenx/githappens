"""GitLab API interactions and glab CLI wrappers."""
import subprocess
import requests
import json
import re
from config import (
    get_api_url, get_gitlab_token, get_group_id,
    get_main_branch, get_squash_commits, get_delete_branch_after_merge,
    get_templates_data,
)

def get_all_projects(project_link):
    url = get_api_url() + "/projects?membership=true&search=" + project_link.split('/')[-1].split('.')[0]
    headers = {"PRIVATE-TOKEN": get_gitlab_token()}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        exit(1)
    else:
        print(f"Request failed with status code {response.status_code}")
        return None

def getAuthorizedUser():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)

def list_epics():
    cmd = f'glab api /groups/{get_group_id()}/epics?per_page=1000&state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)

def list_milestones(current=False):
    import datetime
    cmd = f'glab api /groups/{get_group_id()}/milestones?state=active'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    milestones = json.loads(result.stdout)
    if current:
        today = datetime.date.today().strftime('%Y-%m-%d')
        active = [m for m in milestones
                  if m['start_date'] and m['due_date']
                  and m['start_date'] <= today <= m['due_date']]
        active.sort(key=lambda x: x['due_date'])
        return active[0] if active else None
    return milestones

def getSelectedMilestone(milestone, milestones):
    return next((t for t in milestones if t['title'] == milestone), None)

def get_milestone(manual):
    """Get milestone (auto or manual). Manual selection is triggered via select_milestone_inquirer."""
    if manual:
        ms = list_milestones()
        return getSelectedMilestone(select_milestone_inquirer(ms), ms)
    return list_milestones(True)

def select_milestone_inquirer(milestones):
    """Interactive milestone selection. Call this from templates.py or main.py."""
    import inquirer
    titles = [t['title'] for t in milestones]
    answer = inquirer.prompt([
        inquirer.List('milestones', message="Select milestone:", choices=titles),
    ])
    return answer['milestones']

def list_iterations():
    cmd = f'glab api /groups/{get_group_id()}/iterations?state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)

def getActiveIteration():
    import datetime
    iterations = list_iterations()
    today = datetime.date.today().strftime('%Y-%m-%d')
    active = [i for i in iterations
              if i['start_date'] and i['due_date']
              and i['start_date'] <= today <= i['due_date']]
    active.sort(key=lambda x: x['due_date'])
    return active[0] if active else None

def getSelectedIteration(iteration, iterations):
    return next((t for t in iterations if t['start_date'] + ' - ' + t['due_date'] == iteration), None)

def get_iteration(manual):
    if manual:
        return getSelectedIteration(select_iteration_inquirer(list_iterations()), list_iterations())
    return getActiveIteration()

def select_iteration_inquirer(iterations):
    import inquirer
    opts = [t['start_date'] + ' - ' + t['due_date'] for t in iterations]
    answer = inquirer.prompt([
        inquirer.List('iterations', message="Select iteration:", choices=opts),
    ])
    return answer['iterations']

def getLabelsOfGroup(search=''):
    cmd = f'glab api /groups/{get_group_id()}/labels?search={search}'
    try:
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []

def getCurrentBranch():
    return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()

def create_branch(project_id, issue):
    issueId = str(issue['iid'])
    title = re.sub(r'\s+', '-', issue['title']).lower()
    title = issueId + '-' + title.replace(':','').replace('(',' ').replace(')', '').replace(' ','-')
    branch_output = subprocess.check_output(
        ["glab", "api", f"/projects/{str(project_id)}/repository/branches",
         "-f", f'branch={title}', "-f", f'ref={get_main_branch()}', "-f", f'issue_iid={issueId}']
    )
    return json.loads(branch_output.decode())

def executeIssueCreate(project_id, title, labels, milestoneId, epic, iteration, weight, estimated_time, issue_type='issue'):
    labels = ",".join(labels) if isinstance(labels, list) else labels
    assignee_id = getAuthorizedUser()['id']
    issue_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f'title={title}',
        "-f", f'assignee_ids={assignee_id}',
        "-f", f'issue_type={issue_type}'
    ]
    if labels:
        issue_command.extend(["-f", f'labels={labels}'])
    if weight:
        issue_command.extend(["-f", f'weight={str(weight)}'])
    if milestoneId:
        issue_command.extend(["-f", f'milestone_id={str(milestoneId)}'])
    if epic:
        issue_command.extend(["-f", f'epic_id={str(epic["id"])}'])
    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {str(estimated_time)}m "
    issue_command.extend(["-f", f'description={description}'])
    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())

def createIssue(title, project_id, milestoneId, epic, iteration, settings):
    if settings:
        issueType = settings.get('type') or 'issue'
        return executeIssueCreate(
            project_id, title, settings.get('labels'), milestoneId, epic, iteration,
            settings.get('weight'), settings.get('estimated_time'), issueType
        )
    print("No settings in template")
    exit(2)

def create_merge_request(project_id, branch, issue, labels, milestoneId):
    issueId = str(issue['iid'])
    branch_name = branch['name']
    title = issue['title']
    assignee_id = getAuthorizedUser()['id']
    labels = ",".join(labels) if isinstance(labels, list) else labels
    merge_request_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f", f'title={title}',
        "-f", f'description="Closes #{issueId}"',
        "-f", f'source_branch={branch_name}',
        "-f", f'target_branch={get_main_branch()}',
        "-f", f'issue_iid={issueId}',
        "-f", f'assignee_ids={assignee_id}'
    ]
    if get_squash_commits():
        merge_request_command.extend(["-f", "squash=true"])
    if get_delete_branch_after_merge():
        merge_request_command.extend(["-f", "remove_source_branch=true"])
    if labels:
        merge_request_command.extend(["-f", f'labels={labels}'])
    if milestoneId:
        merge_request_command.extend(["-f", f'milestone_id={str(milestoneId)}'])
    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())

def getMergeRequestForBranch(branchName):
    from config import get_project_id
    project_id = get_project_id()
    api_url = f"{get_api_url()}/projects/{project_id}/merge_requests"
    headers = {"Private-Token": get_gitlab_token()}
    params = {"source_branch": branchName}
    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        for mr in response.json():
            if mr["source_branch"] == branchName:
                return mr
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None

def getActiveMergeRequestId():
    return find_merge_request_id_by_branch(getCurrentBranch())

def find_merge_request_id_by_branch(branch_name):
    return getMergeRequestForBranch(branch_name)['iid']

def addReviewersToMergeRequest(reviewers=None):
    _, REVIEWERS, _ = get_templates_data()
    from config import get_project_id
    project_id = get_project_id()
    mr_id = getActiveMergeRequestId()
    api_url = f"{get_api_url()}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": get_gitlab_token()}
    data = {"reviewer_ids": reviewers if reviewers is not None else REVIEWERS}
    requests.put(api_url, headers=headers, json=data)

def setMergeRequestToAutoMerge():
    from config import get_project_id
    project_id = get_project_id()
    mr_id = getActiveMergeRequestId()
    api_url = f"{get_api_url()}/projects/{project_id}/merge_requests/{mr_id}/merge"
    headers = {"Private-Token": get_gitlab_token()}
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    requests.put(api_url, headers=headers, json=data)

def closeOpenedIssue(issue_iid, project_id):
    subprocess.run(
        ["glab", "api", f"/projects/{project_id}/issues/{issue_iid}", '-X', 'PUT', '-f', 'state_event=close'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

def getCurrentIssueId():
    mr = getMergeRequestForBranch(getCurrentBranch())
    return mr['description'].replace('"','').replace('#','').split()[1]

def get_last_production_deploy():
    import datetime
    _, _, PRODUCTION_MAPPINGS = get_templates_data()
    from config import get_project_id
    try:
        project_id = get_project_id()
        api_url = f"{get_api_url()}/projects/{project_id}/pipelines"
        headers = {"Private-Token": get_gitlab_token()}
        params = {"per_page": 50, "order_by": "updated_at", "sort": "desc"}
        ref = get_main_branch()
        if ref:
            params["ref"] = ref
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
            return
        pipelines = response.json()
        production_pipeline = None
        for pipeline in pipelines:
            detail_url = f"{get_api_url()}/projects/{project_id}/pipelines/{pipeline['id']}/jobs"
            detail_response = requests.get(detail_url, headers=headers)
            if detail_response.status_code == 200:
                for job in detail_response.json():
                    if job.get('status', '').lower() != 'success':
                        continue
                    mapping = PRODUCTION_MAPPINGS.get(str(project_id))
                    if mapping:
                        if (job.get('stage','').lower() == mapping.get('stage','').lower() or
                            job.get('name','').lower() == mapping.get('job','').lower()):
                            production_pipeline = {'pipeline': pipeline, 'production_job': job}
                            break
                    else:
                        print("Didn't find deployment pipeline")
            if production_pipeline:
                break
        if not production_pipeline:
            print("No production deployment found matching pattern")
            return
        p = production_pipeline['pipeline']
        j = production_pipeline['production_job']
        print(f"🚀 Last Production Deployment:")
        print(f"   Pipeline: #{p['id']} - {p['status']}")
        print(f"   Job: {j['name']} ({j['status']})")
        print(f"   Branch/Tag: {p['ref']}")
        print(f"   Started: {j.get('started_at', 'N/A')}")
        print(f"   Finished: {j.get('finished_at', 'N/A')}")
        if j.get('duration'):
            print(f"   Duration: {j['duration']} seconds")
        print(f"   Commit: {p['sha'][:8]}")
        print(f"   URL: {p['web_url']}")
        if j.get('finished_at'):
            try:
                ft = datetime.datetime.fromisoformat(j['finished_at'].replace('Z', '+00:00'))
                td = datetime.datetime.now(datetime.timezone.utc) - ft
                if td.days > 0: print(f"   ⏰ {td.days} days ago")
                elif td.seconds > 3600: print(f"   ⏰ {td.seconds//3600} hours ago")
                else: print(f"   ⏰ {td.seconds//60} minutes ago")
            except: pass
    except Exception as e:
        print(f"Error fetching last production deploy: {str(e)}")