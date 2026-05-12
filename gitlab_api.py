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
    SQUASH_COMMITS,
)


def private_token_headers():
    return {"PRIVATE-TOKEN": GITLAB_TOKEN}


def get_all_projects(project_link):
    url = API_URL + "/projects?membership=true&search=" + project_link.split("/")[-1].split(".")[0]
    response = requests.get(url, headers=private_token_headers())

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
        active_milestones.sort(key=lambda item: item["due_date"])
        return active_milestones[0]
    return milestones


def list_iterations():
    result = subprocess.run(
        ["glab", "api", f"/groups/{GROUP_ID}/iterations?state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def getActiveIteration():
    iterations = list_iterations()
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = []
    for iteration in iterations:
        start_date = iteration["start_date"]
        due_date = iteration["due_date"]
        if start_date and due_date and start_date <= today and due_date >= today:
            active_iterations.append(iteration)
    active_iterations.sort(key=lambda item: item["due_date"])
    return active_iterations[0]


def getAuthorizedUser():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def list_epics():
    result = subprocess.run(
        ["glab", "api", f"/groups/{GROUP_ID}/epics?per_page=1000&state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def get_user(user_id):
    api_url = f"{API_URL}/users/{user_id}"
    response = requests.get(api_url, headers=private_token_headers())
    if response.status_code == 200:
        return response.json()
    return None


def build_issue_command(
    project_id,
    title,
    labels,
    assignee_id,
    milestoneId,
    epic,
    iteration,
    weight,
    estimated_time,
    issue_type="issue",
):
    labels = ",".join(labels) if type(labels) == list else labels
    issue_command = [
        "glab",
        "api",
        f"/projects/{str(project_id)}/issues",
        "-f",
        f"title={title}",
        "-f",
        f"assignee_ids={assignee_id}",
        "-f",
        f"issue_type={issue_type}",
    ]
    if labels:
        issue_command.extend(["-f", f"labels={labels}"])
    if weight:
        issue_command.extend(["-f", f"weight={str(weight)}"])
    if milestoneId:
        issue_command.extend(["-f", f"milestone_id={str(milestoneId)}"])
    if epic:
        issue_command.extend(["-f", f"epic_id={str(epic['id'])}"])

    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    issue_command.extend(["-f", f"description={description}"])
    return issue_command


def executeIssueCreate(
    project_id,
    title,
    labels,
    milestoneId,
    epic,
    iteration,
    weight,
    estimated_time,
    issue_type="issue",
):
    assignee_id = getAuthorizedUser()["id"]
    issue_command = build_issue_command(
        project_id,
        title,
        labels,
        assignee_id,
        milestoneId,
        epic,
        iteration,
        weight,
        estimated_time,
        issue_type,
    )
    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def format_branch_name(issue):
    issue_id = str(issue["iid"])
    title = re.sub("\\s+", "-", issue["title"]).lower()
    title = title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    return f"{issue_id}-{title}"


def create_branch(project_id, issue, main_branch):
    issue_id = str(issue["iid"])
    branch_name = format_branch_name(issue)
    branch_output = subprocess.check_output(
        [
            "glab",
            "api",
            f"/projects/{str(project_id)}/repository/branches",
            "-f",
            f"branch={branch_name}",
            "-f",
            f"ref={main_branch}",
            "-f",
            f"issue_iid={issue_id}",
        ]
    )
    return json.loads(branch_output.decode())


def build_merge_request_command(project_id, branch, issue, labels, milestoneId, assignee_id, main_branch):
    issue_id = str(issue["iid"])
    labels = ",".join(labels) if type(labels) == list else labels
    merge_request_command = [
        "glab",
        "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f",
        f"title={issue['title']}",
        "-f",
        f'description="Closes #{issue_id}"',
        "-f",
        f"source_branch={branch['name']}",
        "-f",
        f"target_branch={main_branch}",
        "-f",
        f"issue_iid={issue_id}",
        "-f",
        f"assignee_ids={assignee_id}",
    ]
    if SQUASH_COMMITS:
        merge_request_command.extend(["-f", "squash=true"])
    if DELETE_BRANCH:
        merge_request_command.extend(["-f", "remove_source_branch=true"])
    if labels:
        merge_request_command.extend(["-f", f"labels={labels}"])
    if milestoneId:
        merge_request_command.extend(["-f", f"milestone_id={str(milestoneId)}"])
    return merge_request_command


def create_merge_request(project_id, branch, issue, labels, milestoneId, main_branch):
    assignee_id = getAuthorizedUser()["id"]
    merge_request_command = build_merge_request_command(
        project_id,
        branch,
        issue,
        labels,
        milestoneId,
        assignee_id,
        main_branch,
    )
    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())


def getMergeRequestForBranch(project_id, branchName):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests"
    params = {"source_branch": branchName}
    response = requests.get(api_url, headers=private_token_headers(), params=params)
    if response.status_code == 200:
        merge_requests = response.json()
        for merge_request in merge_requests:
            if merge_request["source_branch"] == branchName:
                return merge_request
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def addReviewersToMergeRequest(project_id, mr_id, reviewers):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    data = {"reviewer_ids": reviewers}
    requests.put(api_url, headers=private_token_headers(), json=data)


def setMergeRequestToAutoMerge(project_id, mr_id):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}/merge"
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    requests.put(api_url, headers=private_token_headers(), json=data)


def closeOpenedIssue(issue_iid, project_id):
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
    except subprocess.CalledProcessError as error:
        print(f"Error closing issue: {str(error)}")


def getLabelsOfGroup(search=""):
    try:
        result = subprocess.run(
            ["glab", "api", f"/groups/{GROUP_ID}/labels?search={search}"],
            stdout=subprocess.PIPE,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as error:
        print(f"Error getting labels: {str(error)}")
        return []


def get_recent_pipelines(project_id, ref=None, per_page=50):
    api_url = f"{API_URL}/projects/{project_id}/pipelines"
    params = {"per_page": per_page, "order_by": "updated_at", "sort": "desc"}
    if ref:
        params["ref"] = ref
    response = requests.get(api_url, headers=private_token_headers(), params=params)
    if response.status_code != 200:
        print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
        return None
    return response.json()


def get_pipeline_jobs(project_id, pipeline_id):
    api_url = f"{API_URL}/projects/{project_id}/pipelines/{pipeline_id}/jobs"
    response = requests.get(api_url, headers=private_token_headers())
    if response.status_code == 200:
        return response.json()
    return None
