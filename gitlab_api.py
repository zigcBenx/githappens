"""GitLab API interactions (HTTP + glab CLI wrappers)."""
import json
import subprocess

import requests

import config


def _headers():
    return {"PRIVATE-TOKEN": config.GITLAB_TOKEN}


def _private_headers():
    return {"Private-Token": config.GITLAB_TOKEN}


def get_all_projects(project_link):
    url = config.API_URL + "/projects?membership=true&search=" + project_link.split('/')[-1].split('.')[0]
    response = requests.get(url, headers=_headers())

    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        exit(1)
    print(f"Request failed with status code {response.status_code}")
    return None


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def list_milestones():
    cmd = f'glab api /groups/{config.GROUP_ID}/milestones?state=active'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def list_iterations():
    cmd = f'glab api /groups/{config.GROUP_ID}/iterations?state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def list_epics():
    cmd = f'glab api /groups/{config.GROUP_ID}/epics?per_page=1000&state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def get_labels_of_group(search=''):
    cmd = f'glab api /groups/{config.GROUP_ID}/labels?search={search}'
    try:
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []


def get_user(user_id):
    api_url = f"{config.API_URL}/users/{user_id}"
    response = requests.get(api_url, headers=_private_headers())
    if response.status_code == 200:
        return response.json()
    return None


def get_merge_requests(project_id, params):
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests"
    response = requests.get(api_url, headers=_private_headers(), params=params)
    if response.status_code == 200:
        return response.json()
    print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def update_merge_request(project_id, mr_id, data):
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    return requests.put(api_url, headers=_private_headers(), json=data)


def merge_merge_request(project_id, mr_id, data):
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests/{mr_id}/merge"
    return requests.put(api_url, headers=_private_headers(), json=data)


def list_pipelines(project_id, params):
    api_url = f"{config.API_URL}/projects/{project_id}/pipelines"
    return requests.get(api_url, headers=_private_headers(), params=params)


def list_pipeline_jobs(project_id, pipeline_id):
    api_url = f"{config.API_URL}/projects/{project_id}/pipelines/{pipeline_id}/jobs"
    return requests.get(api_url, headers=_private_headers())


def create_issue_via_glab(project_id, fields):
    """Run `glab api` to create an issue with -f key=value fields."""
    cmd = ["glab", "api", f"/projects/{str(project_id)}/issues"]
    for k, v in fields:
        cmd.extend(["-f", f"{k}={v}"])
    output = subprocess.check_output(cmd)
    return json.loads(output.decode())


def create_branch_via_glab(project_id, branch_name, ref, issue_iid):
    cmd = [
        "glab", "api",
        f"/projects/{str(project_id)}/repository/branches",
        "-f", f"branch={branch_name}",
        "-f", f"ref={ref}",
        "-f", f"issue_iid={issue_iid}",
    ]
    output = subprocess.check_output(cmd)
    return json.loads(output.decode())


def create_merge_request_via_glab(project_id, fields):
    cmd = ["glab", "api", f"/projects/{str(project_id)}/merge_requests"]
    for k, v in fields:
        cmd.extend(["-f", f"{k}={v}"])
    output = subprocess.check_output(cmd)
    return json.loads(output.decode())


def close_issue(project_id, issue_iid):
    cmd = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        "-X", "PUT",
        "-f", "state_event=close",
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {str(e)}")


def add_spent_time(project_id, issue_iid, minutes):
    cmd = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}/add_spent_time",
        "-f", f"duration={minutes}m",
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error adding time tracking: {str(e)}")
        return False


def add_issue_note(project_id, issue_iid, body):
    cmd = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}/notes",
        "-f", f"body={body}",
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
