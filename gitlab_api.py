#!/usr/bin/env python3
import json
import subprocess

import requests

import config


def _headers():
    return {"Private-Token": config.GITLAB_TOKEN}


def _glab(*args):
    """Run a glab CLI command and return parsed JSON output."""
    cmd = ["glab", "api"] + list(args)
    result = subprocess.check_output(cmd)
    return json.loads(result.decode())


def _glab_raw(*args):
    """Run a glab CLI command and return raw stdout bytes."""
    cmd = ["glab", "api"] + list(args)
    return subprocess.check_output(cmd)


def _api_get(path, params=None):
    url = config.API_URL + path
    response = requests.get(url, headers=_headers(), params=params)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        exit(1)
    else:
        print(f"Request failed with status code {response.status_code}")
        return None


def _api_post(path, data=None, json_data=None):
    url = config.API_URL + path
    response = requests.post(url, headers=_headers(), data=data, json=json_data)
    return response


def _api_put(path, data=None, json_data=None):
    url = config.API_URL + path
    response = requests.put(url, headers=_headers(), data=data, json=json_data)
    return response


def get_project_id():
    import git_utils
    project_link = git_utils.get_project_link_from_current_dir()
    if project_link == -1:
        while True:
            project_id = input('Please enter the ID of your GitLab project: ')
            if project_id:
                return project_id
            exit('Invalid project ID.')

    all_projects = get_all_projects(project_link)
    matching_id = None
    for project in all_projects:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def get_all_projects(project_link):
    search_term = project_link.split('/')[-1].split('.')[0]
    path = f"/projects?membership=true&search={search_term}"
    return _api_get(path)


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def list_milestones(current=False):
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.GROUP_ID}/milestones?state=active"],
        stdout=subprocess.PIPE,
    )
    milestones = json.loads(result.stdout)
    if current:
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        active = [
            m for m in milestones
            if m.get('start_date') and m.get('due_date')
            and m['start_date'] <= today and m['due_date'] >= today
        ]
        active.sort(key=lambda x: x['due_date'])
        return active[0] if active else None
    return milestones


def list_iterations():
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.GROUP_ID}/iterations?state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def get_active_iteration():
    import datetime
    iterations = list_iterations()
    today = datetime.date.today().strftime('%Y-%m-%d')
    active = [
        i for i in iterations
        if i.get('start_date') and i.get('due_date')
        and i['start_date'] <= today and i['due_date'] >= today
    ]
    active.sort(key=lambda x: x['due_date'])
    return active[0] if active else None


def list_epics():
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.GROUP_ID}/epics?per_page=1000&state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def execute_issue_create(project_id, title, labels, milestone_id, epic, iteration, weight, estimated_time, issue_type='issue'):
    labels = ",".join(labels) if isinstance(labels, list) else labels
    assignee_id = get_authorized_user()['id']
    cmd = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f'title={title}',
        "-f", f'assignee_ids={assignee_id}',
        "-f", f'issue_type={issue_type}',
    ]
    if labels:
        cmd.extend(["-f", f'labels={labels}'])
    if weight:
        cmd.extend(["-f", f'weight={str(weight)}'])
    if milestone_id:
        cmd.extend(["-f", f'milestone_id={str(milestone_id)}'])
    if epic:
        cmd.extend(["-f", f'epic_id={str(epic["id"])}'])

    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "

    cmd.extend(["-f", f'description={description}'])
    output = subprocess.check_output(cmd)
    return json.loads(output.decode())


def create_branch(project_id, issue):
    import re
    issue_id = str(issue['iid'])
    title = re.sub(r'\s+', '-', issue['title']).lower()
    title = issue_id + '-' + title.replace(':', '').replace('(', ' ').replace(')', '').replace(' ', '-')
    output = subprocess.check_output([
        "glab", "api",
        f"/projects/{str(project_id)}/repository/branches",
        "-f", f'branch={title}',
        "-f", f'ref={config.MAIN_BRANCH}',
        "-f", f'issue_iid={issue_id}',
    ])
    return json.loads(output.decode())


def create_merge_request(project_id, branch, issue, labels, milestone_id):
    issue_id = str(issue['iid'])
    branch_name = branch['name']
    title = issue['title']
    assignee_id = get_authorized_user()['id']
    labels = ",".join(labels) if isinstance(labels, list) else labels
    cmd = [
        "glab", "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f", f'title={title}',
        "-f", f'description="Closes #{issue_id}"',
        "-f", f'source_branch={branch_name}',
        "-f", f'target_branch={config.MAIN_BRANCH}',
        "-f", f'issue_iid={issue_id}',
        "-f", f'assignee_ids={assignee_id}',
    ]
    if config.SQUASH_COMMITS:
        cmd.extend(["-f", "squash=true"])
    if config.DELETE_BRANCH:
        cmd.extend(["-f", "remove_source_branch=true"])
    if labels:
        cmd.extend(["-f", f'labels={labels}'])
    if milestone_id:
        cmd.extend(["-f", f'milestone_id={str(milestone_id)}'])

    output = subprocess.check_output(cmd)
    return json.loads(output.decode())


def get_merge_request_for_branch(branch_name):
    project_id = get_project_id()
    path = f"/projects/{project_id}/merge_requests"
    params = {"source_branch": branch_name}
    response = requests.get(config.API_URL + path, headers=_headers(), params=params)
    if response.status_code == 200:
        merge_requests = response.json()
        for mr in merge_requests:
            if mr.get("source_branch") == branch_name:
                return mr
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def get_active_merge_request_id():
    import git_utils
    branch = git_utils.get_current_branch()
    mr = get_merge_request_for_branch(branch)
    return mr['iid'] if mr else None


def add_reviewers_to_merge_request(reviewers=None):
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    path = f"/projects/{project_id}/merge_requests/{mr_id}"
    data = {"reviewer_ids": reviewers if reviewers is not None else config.REVIEWERS}
    _api_put(path, json_data=data)


def set_merge_request_to_auto_merge():
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    path = f"/projects/{project_id}/merge_requests/{mr_id}/merge"
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    _api_put(path, json_data=data)


def get_labels_of_group(search=''):
    cmd = ["glab", "api", f"/groups/{config.GROUP_ID}/labels?search={search}"]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []


def close_opened_issue(issue_iid, project_id):
    cmd = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        '-X', 'PUT',
        '-f', 'state_event=close',
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {str(e)}")


def track_issue_time(project_id, issue_id, spent_time):
    cmd = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_id}/notes",
        "-f", f"body=/spend {spent_time}m",
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except subprocess.CalledProcessError as e:
        print(f"Error adding time tracking: {str(e)}")
    except Exception as e:
        print(f"Error tracking issue time: {str(e)}")


def add_spent_time(project_id, issue_iid, minutes):
    cmd = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}/add_spent_time",
        "-f", f"duration={minutes}m",
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error adding time tracking: {str(e)}")


def get_pipelines(project_id, params):
    path = f"/projects/{project_id}/pipelines"
    return _api_get(path, params=params)


def get_pipeline_jobs(project_id, pipeline_id):
    path = f"/projects/{project_id}/pipelines/{pipeline_id}/jobs"
    response = requests.get(config.API_URL + path, headers=_headers())
    if response.status_code == 200:
        return response.json()
    return None


def get_user_details(user_id):
    path = f"/users/{user_id}"
    response = requests.get(config.API_URL + path, headers=_headers())
    if response.status_code == 200:
        return response.json()
    return None


def get_merge_request_changes(project_id, mr_id):
    path = f"/projects/{project_id}/merge_requests/{mr_id}/changes"
    response = requests.get(config.API_URL + path, headers=_headers())
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get MR changes: {response.status_code}")
        return None


def get_diff_refs(project_id, mr_id):
    path = f"/projects/{project_id}/merge_requests/{mr_id}"
    response = requests.get(config.API_URL + path, headers=_headers())
    if response.status_code == 200:
        mr_data = response.json()
        diff_refs = mr_data.get('diff_refs', {})
        return {
            'base_sha': diff_refs.get('base_sha'),
            'head_sha': diff_refs.get('head_sha'),
            'start_sha': diff_refs.get('start_sha'),
        }
    return None


def post_inline_comment(project_id, mr_id, body, diff_refs, file_path, line):
    path = f"/projects/{project_id}/merge_requests/{mr_id}/discussions"
    data = {
        "body": body,
        "position": {
            "base_sha": diff_refs['base_sha'],
            "head_sha": diff_refs['head_sha'],
            "start_sha": diff_refs['start_sha'],
            "position_type": "text",
            "new_path": file_path,
            "new_line": line,
        },
    }
    response = requests.post(config.API_URL + path, headers=_headers(), json=data)
    return response.status_code == 201


def post_to_merge_request(comment_body, project_id, mr_id):
    path = f"/projects/{project_id}/merge_requests/{mr_id}/notes"
    data = {"body": comment_body}
    response = requests.post(config.API_URL + path, headers=_headers(), json=data)
    if response.status_code == 201:
        print("AI review summary posted to merge request")
        return True
    else:
        print(f"Failed to post comment: {response.status_code}")
        print(response.text)
        return False
