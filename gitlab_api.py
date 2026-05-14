import datetime
import json
import re
import subprocess
import requests

from config import BASE_URL, API_URL, GROUP_ID, GITLAB_TOKEN, MAIN_BRANCH, SQUASH_COMMITS, DELETE_BRANCH, PRODUCTION_PIPELINE_NAME, PRODUCTION_JOB_NAME, PRODUCTION_REF
from git_utils import getCurrentBranch, getProjectLinkFromCurrentDir


def api_headers():
    return {'Private-Token': GITLAB_TOKEN}


def get_all_projects(project_link):
    url = API_URL + "/projects?membership=true&search=" + project_link.split('/')[-1].split('.')[0]

    headers = {
        "PRIVATE-TOKEN": GITLAB_TOKEN
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

def list_iterations():
    cmd = f'glab api /groups/{GROUP_ID}/iterations?state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    iterations = json.loads(result.stdout)
    return iterations

def getAuthorizedUser():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)

def list_epics():
    cmd = f'glab api /groups/{GROUP_ID}/epics?per_page=1000&state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)

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

def getLabelsOfGroup(search=''):
    cmd = f'glab api /groups/{GROUP_ID}/labels?search={search}'
    try:
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []

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
        if MAIN_BRANCH:
            params["ref"] = MAIN_BRANCH
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
            print(f"No production deployment found matching pattern")
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

def getActiveMergeRequestId():
    branch_to_find = getCurrentBranch()
    return find_merge_request_id_by_branch(branch_to_find)

def find_merge_request_id_by_branch(branch_name):
    return getMergeRequestForBranch(branch_name)['iid']

def getCurrentIssueId():
    mr = getMergeRequestForBranch(getCurrentBranch())
    return mr['description'].replace('"','').replace('#','').split()[1]

