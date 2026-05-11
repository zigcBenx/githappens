import datetime
import json
import subprocess
import sys

from .config import get_settings
from .git_utils import get_project_link_from_current_dir, issue_branch_name
from .interactive import enter_project_id
from .templates import get_reviewers, normalize_labels


def _requests():
    import requests

    return requests


def get_project_id():
    project_link = get_project_link_from_current_dir()
    if project_link == -1:
        return enter_project_id()

    all_projects = get_all_projects(project_link)
    matching_id = None
    for project in all_projects:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def get_all_projects(project_link):
    requests = _requests()
    settings = get_settings()
    url = settings.api_url + "/projects?membership=true&search=" + project_link.split("/")[-1].split(".")[0]
    headers = {"PRIVATE-TOKEN": settings.gitlab_token}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        sys.exit(1)

    print(f"Request failed with status code {response.status_code}")
    return None


def list_milestones(current=False):
    settings = get_settings()
    cmd = f"glab api /groups/{settings.group_id}/milestones?state=active"
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
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
    settings = get_settings()
    cmd = f"glab api /groups/{settings.group_id}/iterations?state=opened"
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
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
    active_iterations.sort(key=lambda item: item["due_date"])
    return active_iterations[0]


def list_epics():
    settings = get_settings()
    cmd = f"glab api /groups/{settings.group_id}/epics?per_page=1000&state=opened"
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def create_issue(title, project_id, milestone_id, epic, iteration, settings):
    if settings:
        issue_type = settings.get("type") or "issue"
        return execute_issue_create(
            project_id,
            title,
            settings.get("labels"),
            milestone_id,
            epic,
            iteration,
            settings.get("weight"),
            settings.get("estimated_time"),
            issue_type,
        )
    print("No settings in template")
    sys.exit(2)


def execute_issue_create(project_id, title, labels, milestone_id, epic, iteration, weight, estimated_time, issue_type="issue"):
    labels = normalize_labels(labels)
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


def create_branch(project_id, issue, main_branch):
    branch_output = subprocess.check_output([
        "glab", "api",
        f"/projects/{str(project_id)}/repository/branches",
        "-f", f"branch={issue_branch_name(issue)}",
        "-f", f"ref={main_branch}",
        "-f", f"issue_iid={str(issue['iid'])}",
    ])
    return json.loads(branch_output.decode())


def create_merge_request(project_id, branch, issue, labels, milestone_id, main_branch):
    settings = get_settings()
    issue_id = str(issue["iid"])
    labels = normalize_labels(labels)
    assignee_id = get_authorized_user()["id"]
    merge_request_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f", f"title={issue['title']}",
        "-f", f"description=\"Closes #{issue_id}\"",
        "-f", f"source_branch={branch['name']}",
        "-f", f"target_branch={main_branch}",
        "-f", f"issue_iid={issue_id}",
        "-f", f"assignee_ids={assignee_id}",
    ]

    if settings.squash_commits:
        merge_request_command.extend(["-f", "squash=true"])

    if settings.delete_branch_after_merge:
        merge_request_command.extend(["-f", "remove_source_branch=true"])

    if labels:
        merge_request_command.extend(["-f", f"labels={labels}"])

    if milestone_id:
        merge_request_command.extend(["-f", f"milestone_id={str(milestone_id)}"])

    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())


def get_merge_request_for_branch(branch_name):
    requests = _requests()
    settings = get_settings()
    project_id = get_project_id()
    api_url = f"{settings.api_url}/projects/{project_id}/merge_requests"
    headers = {"Private-Token": settings.gitlab_token}
    params = {"source_branch": branch_name}

    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        merge_requests = response.json()
        for merge_request in merge_requests:
            if merge_request["source_branch"] == branch_name:
                return merge_request
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def find_merge_request_id_by_branch(branch_name):
    return get_merge_request_for_branch(branch_name)["iid"]


def get_active_merge_request_id(branch_name):
    return find_merge_request_id_by_branch(branch_name)


def add_reviewers_to_merge_request(branch_name, reviewers=None):
    requests = _requests()
    settings = get_settings()
    project_id = get_project_id()
    mr_id = get_active_merge_request_id(branch_name)
    api_url = f"{settings.api_url}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": settings.gitlab_token}
    if reviewers is None:
        reviewers = get_reviewers()
    data = {"reviewer_ids": reviewers}
    requests.put(api_url, headers=headers, json=data)


def set_merge_request_to_auto_merge(branch_name):
    requests = _requests()
    settings = get_settings()
    project_id = get_project_id()
    mr_id = get_active_merge_request_id(branch_name)
    api_url = f"{settings.api_url}/projects/{project_id}/merge_requests/{mr_id}/merge"
    headers = {"Private-Token": settings.gitlab_token}
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    requests.put(api_url, headers=headers, json=data)


def close_opened_issue(issue_iid, project_id):
    issue_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        "-X", "PUT",
        "-f", "state_event=close",
    ]
    try:
        subprocess.run(issue_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        print(f"Error closing issue: {str(error)}")


def get_labels_of_group(search=""):
    settings = get_settings()
    cmd = f"glab api /groups/{settings.group_id}/labels?search={search}"
    try:
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as error:
        print(f"Error getting labels: {str(error)}")
        return []


getActiveIteration = get_active_iteration
getAuthorizedUser = get_authorized_user
createIssue = create_issue
executeIssueCreate = execute_issue_create
getMergeRequestForBranch = get_merge_request_for_branch
closeOpenedIssue = close_opened_issue
getLabelsOfGroup = get_labels_of_group
