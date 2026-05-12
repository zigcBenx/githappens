import datetime
import json
import re
import subprocess

import requests

from config import CONFIG, REVIEWERS
from git_utils import get_current_branch, get_project_link_from_current_dir


MAIN_BRANCH = "master"


def set_main_branch(branch_name):
    global MAIN_BRANCH
    MAIN_BRANCH = branch_name


def enter_project_id():
    from interactive import enter_project_id as prompt_enter_project_id

    return prompt_enter_project_id()


def get_project_id():
    project_link = get_project_link_from_current_dir()
    if project_link == -1:
        return enter_project_id()

    all_projects = get_all_projects(project_link)
    matching_id = None
    for project in all_projects or []:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def get_all_projects(project_link):
    url = CONFIG.api_url + "/projects?membership=true&search=" + project_link.split("/")[-1].split(".")[0]
    headers = {"PRIVATE-TOKEN": CONFIG.gitlab_token}
    response = requests.get(url, headers=headers)

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
        ["glab", "api", f"/groups/{CONFIG.group_id}/milestones?state=active"],
        stdout=subprocess.PIPE,
    )
    milestones = json.loads(result.stdout)
    if current:
        today = datetime.date.today().strftime("%Y-%m-%d")
        active_milestones = [
            milestone
            for milestone in milestones
            if milestone["start_date"]
            and milestone["due_date"]
            and milestone["start_date"] <= today <= milestone["due_date"]
        ]
        active_milestones.sort(key=lambda item: item["due_date"])
        return active_milestones[0]
    return milestones


def list_iterations():
    result = subprocess.run(
        ["glab", "api", f"/groups/{CONFIG.group_id}/iterations?state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def get_active_iteration():
    iterations = list_iterations()
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = [
        iteration
        for iteration in iterations
        if iteration["start_date"]
        and iteration["due_date"]
        and iteration["start_date"] <= today <= iteration["due_date"]
    ]
    active_iterations.sort(key=lambda item: item["due_date"])
    return active_iterations[0]


def list_epics():
    result = subprocess.run(
        ["glab", "api", f"/groups/{CONFIG.group_id}/epics?per_page=1000&state=opened"],
        stdout=subprocess.PIPE,
    )
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
    exit(2)


def execute_issue_create(
    project_id,
    title,
    labels,
    milestone_id,
    epic,
    iteration,
    weight,
    estimated_time,
    issue_type="issue",
):
    labels = ",".join(labels) if type(labels) == list else labels
    assignee_id = get_authorized_user()["id"]
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


def create_branch(project_id, issue):
    issue_id = str(issue["iid"])
    title = re.sub("\\s+", "-", issue["title"]).lower()
    title = issue_id + "-" + title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    branch_output = subprocess.check_output(
        [
            "glab",
            "api",
            f"/projects/{str(project_id)}/repository/branches",
            "-f",
            f"branch={title}",
            "-f",
            f"ref={MAIN_BRANCH}",
            "-f",
            f"issue_iid={issue_id}",
        ]
    )
    return json.loads(branch_output.decode())


def create_merge_request(project_id, branch, issue, labels, milestone_id):
    issue_id = str(issue["iid"])
    branch = branch["name"]
    title = issue["title"]
    assignee_id = get_authorized_user()["id"]
    labels = ",".join(labels) if type(labels) == list else labels
    merge_request_command = [
        "glab",
        "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f",
        f"title={title}",
        "-f",
        f'description="Closes #{issue_id}"',
        "-f",
        f"source_branch={branch}",
        "-f",
        f"target_branch={MAIN_BRANCH}",
        "-f",
        f"issue_iid={issue_id}",
        "-f",
        f"assignee_ids={assignee_id}",
    ]

    if CONFIG.squash_commits:
        merge_request_command.extend(["-f", "squash=true"])
    if CONFIG.delete_branch_after_merge:
        merge_request_command.extend(["-f", "remove_source_branch=true"])
    if labels:
        merge_request_command.extend(["-f", f"labels={labels}"])
    if milestone_id:
        merge_request_command.extend(["-f", f"milestone_id={str(milestone_id)}"])

    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())


def get_merge_request_for_branch(branch_name):
    project_id = get_project_id()
    api_url = f"{CONFIG.api_url}/projects/{project_id}/merge_requests"
    headers = {"Private-Token": CONFIG.gitlab_token}
    response = requests.get(api_url, headers=headers, params={"source_branch": branch_name})

    if response.status_code == 200:
        for merge_request in response.json():
            if merge_request["source_branch"] == branch_name:
                return merge_request
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def find_merge_request_id_by_branch(branch_name):
    return get_merge_request_for_branch(branch_name)["iid"]


def get_active_merge_request_id():
    return find_merge_request_id_by_branch(get_current_branch())


def add_reviewers_to_merge_request(reviewers=None):
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    api_url = f"{CONFIG.api_url}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": CONFIG.gitlab_token}
    data = {"reviewer_ids": reviewers if reviewers is not None else REVIEWERS}
    requests.put(api_url, headers=headers, json=data)


def set_merge_request_to_auto_merge():
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    api_url = f"{CONFIG.api_url}/projects/{project_id}/merge_requests/{mr_id}/merge"
    headers = {"Private-Token": CONFIG.gitlab_token}
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


def get_labels_of_group(search=""):
    try:
        result = subprocess.run(
            ["glab", "api", f"/groups/{CONFIG.group_id}/labels?search={search}"],
            stdout=subprocess.PIPE,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as error:
        print(f"Error getting labels: {str(error)}")
        return []


# Backwards-compatible names.
get_project_id = get_project_id
get_all_projects = get_all_projects
enterProjectId = enter_project_id
list_milestones = list_milestones
list_iterations = list_iterations
getActiveIteration = get_active_iteration
getAuthorizedUser = get_authorized_user
list_epics = list_epics
createIssue = create_issue
executeIssueCreate = execute_issue_create
create_branch = create_branch
create_merge_request = create_merge_request
getMergeRequestForBranch = get_merge_request_for_branch
find_merge_request_id_by_branch = find_merge_request_id_by_branch
getActiveMergeRequestId = get_active_merge_request_id
addReviewersToMergeRequest = add_reviewers_to_merge_request
setMergeRequestToAutoMerge = set_merge_request_to_auto_merge
closeOpenedIssue = close_opened_issue
getLabelsOfGroup = get_labels_of_group
