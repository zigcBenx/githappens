import json
import subprocess

import requests

from . import config as settings


def private_token_headers():
    return {"Private-Token": settings.GITLAB_TOKEN}


def get_all_projects(project_link):
    url = f"{settings.API_URL}/projects?membership=true&search={project_link.split('/')[-1].split('.')[0]}"
    response = requests.get(url, headers={"PRIVATE-TOKEN": settings.GITLAB_TOKEN})

    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        raise SystemExit(1)

    print(f"Request failed with status code {response.status_code}")
    return None


def list_milestones():
    result = subprocess.run(
        f"glab api /groups/{settings.GROUP_ID}/milestones?state=active".split(),
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def list_iterations():
    result = subprocess.run(
        f"glab api /groups/{settings.GROUP_ID}/iterations?state=opened".split(),
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def list_epics():
    result = subprocess.run(
        f"glab api /groups/{settings.GROUP_ID}/epics?per_page=1000&state=opened".split(),
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def get_labels_of_group(search=""):
    try:
        result = subprocess.run(
            f"glab api /groups/{settings.GROUP_ID}/labels?search={search}".split(),
            stdout=subprocess.PIPE,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as exc:
        print(f"Error getting labels: {str(exc)}")
        return []


def get_merge_request_for_branch(project_id, branch_name):
    response = requests.get(
        f"{settings.API_URL}/projects/{project_id}/merge_requests",
        headers=private_token_headers(),
        params={"source_branch": branch_name},
    )
    if response.status_code == 200:
        for merge_request in response.json():
            if merge_request["source_branch"] == branch_name:
                return merge_request
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def close_opened_issue(issue_iid, project_id):
    issue_command = [
        "glab",
        "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        "-X",
        "PUT",
        "-f",
        "state_event=close",
    ]
    try:
        subprocess.run(issue_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        print(f"Error closing issue: {str(exc)}")

