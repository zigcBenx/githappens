import subprocess
import json
import datetime
import requests
import config


def get_all_projects(project_link):
    url = config.API_URL + "/projects?membership=true&search=" + project_link.split('/')[-1].split('.')[0]

    headers = {
        "PRIVATE-TOKEN": config.GITLAB_TOKEN
    }

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


def list_milestones(current=False):
    cmd = f'glab api /groups/{config.GROUP_ID}/milestones?state=active'
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


def list_iterations():
    cmd = f'glab api /groups/{config.GROUP_ID}/iterations?state=opened'
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


def list_epics():
    cmd = f'glab api /groups/{config.GROUP_ID}/epics?per_page=1000&state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def getLabelsOfGroup(search=''):
    cmd = f'glab api /groups/{config.GROUP_ID}/labels?search={search}'
    try:
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []


def getMergeRequestForBranch(project_id, branchName):
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests"
    headers = {"Private-Token": config.GITLAB_TOKEN}

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


def addReviewersToMergeRequest(project_id, mr_id, reviewers=None):
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": config.GITLAB_TOKEN}

    data = {
        "reviewer_ids": reviewers if reviewers is not None else config.REVIEWERS
    }

    requests.put(api_url, headers=headers, json=data)


def setMergeRequestToAutoMerge(project_id, mr_id):
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests/{mr_id}/merge"
    headers = {"Private-Token": config.GITLAB_TOKEN}

    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }

    requests.put(api_url, headers=headers, json=data)


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

    description = ""
    if iteration:
        iterationId = iteration['id']
        description += f"/iteration *iteration:{str(iterationId)} "

    if estimated_time:
        description += f"\n/estimate {estimated_time}m "

    issue_command.extend(["-f", f'description={description}'])

    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_branch(project_id, issue):
    issueId = str(issue['iid'])
    title = '-'.join(issue['title'].split()).lower()
    title = issueId + '-' + title.replace(':','').replace('(',' ').replace(')', '').replace(' ','-')
    branch_output = subprocess.check_output(["glab", "api", f"/projects/{str(project_id)}/repository/branches", "-f", f'branch={title}', "-f", f'ref={config.MAIN_BRANCH}', "-f", f'issue_iid={issueId}'])
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
        "-f", f'target_branch={config.MAIN_BRANCH}',
        "-f", f'issue_iid={issueId}',
        "-f", f'assignee_ids={assignee_id}'
    ]

    if config.SQUASH_COMMITS:
        merge_request_command.append("-f")
        merge_request_command.append("squash=true")

    if config.DELETE_BRANCH:
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


def get_last_production_deploy_info(project_id, ref=None):
    """
    Scan pipelines/jobs for the last successful production deploy.
    Returns dict with 'pipeline' and 'production_job', or {'error': ...}.
    No printing — callers handle display.
    """
    api_url = f"{config.API_URL}/projects/{project_id}/pipelines"
    headers = {"Private-Token": config.GITLAB_TOKEN}

    params = {
        "per_page": 50,
        "order_by": "updated_at",
        "sort": "desc"
    }

    if ref is not None:
        params["ref"] = ref
    elif config.MAIN_BRANCH:
        params["ref"] = config.MAIN_BRANCH
    else:
        params["ref"] = "main"

    response = requests.get(api_url, headers=headers, params=params)

    if response.status_code != 200:
        return {'error': 'pipelines_fetch', 'status': response.status_code, 'text': response.text}

    pipelines = response.json()
    production_pipeline = None

    for pipeline in pipelines:
        pipeline_detail_url = f"{config.API_URL}/projects/{project_id}/pipelines/{pipeline['id']}/jobs"
        detail_response = requests.get(pipeline_detail_url, headers=headers)

        if detail_response.status_code == 200:
            jobs = detail_response.json()

            for job in jobs:
                job_name = job.get('name', '')
                stage = job.get('stage', '')
                job_status = job.get('status', '').lower()

                if job_status != 'success':
                    continue

                project_mapping = config.PRODUCTION_MAPPINGS.get(str(project_id))
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

        if production_pipeline:
            break

    if not production_pipeline:
        return {'error': 'not_found'}

    return {
        'pipeline': production_pipeline['pipeline'],
        'production_job': production_pipeline['production_job'],
    }
