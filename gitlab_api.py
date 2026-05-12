import datetime
import json
import re
import subprocess

import requests

from config import (
    API_URL,
    DELETE_BRANCH,
    GITLAB_TOKEN,
    GROUP_ID,
    MAIN_BRANCH,
    REVIEWERS,
    SQUASH_COMMITS,
)


def private_token_headers():
    return {"Private-Token": GITLAB_TOKEN}


def get_all_projects(project_link):
    url = f"{API_URL}/projects?membership=true&search={project_link.split('/')[-1].split('.')[0]}"
    response = requests.get(url, headers={"PRIVATE-TOKEN": GITLAB_TOKEN})

    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        exit(1)

    print(f"Request failed with status code {response.status_code}")
    return None


def list_milestones(current=False):
    result = subprocess.run(
        ["glab", "api", f"/groups/{GROUP_ID}/milestones?state=active"],
        stdout=subprocess.PIPE,
    )
    milestones = json.loads(result.stdout)
    if current:
        today = datetime.date.today().strftime("%Y-%m-%d")
        active_milestones = []
        for milestone in milestones:
            start_date = milestone["start_date"]
            due_date = milestone["due_date"]
            if start_date and due_date and start_date <= today and due_date >= today:
                active_milestones.append(milestone)
        active_milestones.sort(key=lambda milestone: milestone["due_date"])
        return active_milestones[0]
    return milestones


def list_iterations():
    result = subprocess.run(
        ["glab", "api", f"/groups/{GROUP_ID}/iterations?state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def get_active_iteration():
    iterations = list_iterations()
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = []
    for iteration in iterations:
        start_date = iteration["start_date"]
        due_date = iteration["due_date"]
        if start_date and due_date and start_date <= today and due_date >= today:
            active_iterations.append(iteration)
    active_iterations.sort(key=lambda iteration: iteration["due_date"])
    return active_iterations[0]


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def list_epics():
    result = subprocess.run(
        ["glab", "api", f"/groups/{GROUP_ID}/epics?per_page=1000&state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def create_issue(project_id, title, labels, milestone_id, epic, iteration, weight, estimated_time, issue_type="issue"):
    labels = ",".join(labels) if type(labels) == list else labels
    assignee_id = get_authorized_user()["id"]
    issue_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f"title={title}",
        "-f", f"assignee_ids={assignee_id}",
        "-f", f"issue_type={issue_type}",
    ]
    if labels:
        issue_command.extend(["-f", f"labels={labels}"])

    if weight:
        issue_command.extend(["-f", f"weight={str(weight)}"])

    if milestone_id:
        issue_command.extend(["-f", f"milestone_id={str(milestone_id)}"])

    if epic:
        issue_command.extend(["-f", f"epic_id={str(epic['id'])}"])

    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "

    if estimated_time:
        description += f"\n/estimate {estimated_time}m "

    issue_command.extend(["-f", f"description={description}"])
    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_branch(project_id, issue, main_branch=MAIN_BRANCH):
    issue_id = str(issue["iid"])
    title = re.sub("\\s+", "-", issue["title"]).lower()
    title = issue_id + "-" + title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    branch_output = subprocess.check_output([
        "glab", "api",
        f"/projects/{str(project_id)}/repository/branches",
        "-f", f"branch={title}",
        "-f", f"ref={main_branch}",
        "-f", f"issue_iid={issue_id}",
    ])
    return json.loads(branch_output.decode())


def create_merge_request(project_id, branch, issue, labels, milestone_id, main_branch=MAIN_BRANCH):
    issue_id = str(issue["iid"])
    branch_name = branch["name"]
    assignee_id = get_authorized_user()["id"]
    labels = ",".join(labels) if type(labels) == list else labels
    merge_request_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f", f"title={issue['title']}",
        "-f", f"description=\"Closes #{issue_id}\"",
        "-f", f"source_branch={branch_name}",
        "-f", f"target_branch={main_branch}",
        "-f", f"issue_iid={issue_id}",
        "-f", f"assignee_ids={assignee_id}",
    ]

    if SQUASH_COMMITS:
        merge_request_command.extend(["-f", "squash=true"])

    if DELETE_BRANCH:
        merge_request_command.extend(["-f", "remove_source_branch=true"])

    if labels:
        merge_request_command.extend(["-f", f"labels={labels}"])

    if milestone_id:
        merge_request_command.extend(["-f", f"milestone_id={str(milestone_id)}"])

    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())


def get_merge_request_for_branch(project_id, branch_name):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests"
    response = requests.get(api_url, headers=private_token_headers(), params={"source_branch": branch_name})
    if response.status_code == 200:
        merge_requests = response.json()
        for merge_request in merge_requests:
            if merge_request["source_branch"] == branch_name:
                return merge_request
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def get_user(reviewer_id):
    response = requests.get(f"{API_URL}/users/{reviewer_id}", headers=private_token_headers())
    if response.status_code == 200:
        return response.json()
    return None


def add_reviewers_to_merge_request(project_id, mr_id, reviewers=None):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    data = {"reviewer_ids": reviewers if reviewers is not None else REVIEWERS}
    requests.put(api_url, headers=private_token_headers(), json=data)


def set_merge_request_to_auto_merge(project_id, mr_id):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}/merge"
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    requests.put(api_url, headers=private_token_headers(), json=data)


def close_issue(issue_iid, project_id):
    issue_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        "-X", "PUT",
        "-f", "state_event=close",
    ]
    try:
        subprocess.run(issue_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {str(e)}")


def add_spent_time(issue_iid, project_id, minutes):
    time_tracking_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}/add_spent_time",
        "-f", f"duration={minutes}m",
    ]
    subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def add_issue_time_note(project_id, issue_id, spent_time):
    time_tracking_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_id}/notes",
        "-f", f"body=/spend {spent_time}m",
    ]
    subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


def get_labels_of_group(search=""):
    try:
        result = subprocess.run(
            ["glab", "api", f"/groups/{GROUP_ID}/labels?search={search}"],
            stdout=subprocess.PIPE,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []


def list_pipelines(project_id, params):
    response = requests.get(f"{API_URL}/projects/{project_id}/pipelines", headers=private_token_headers(), params=params)
    if response.status_code != 200:
        print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
        return None
    return response.json()


def list_pipeline_jobs(project_id, pipeline_id):
    response = requests.get(f"{API_URL}/projects/{project_id}/pipelines/{pipeline_id}/jobs", headers=private_token_headers())
    if response.status_code == 200:
        return response.json()
    return None
