import datetime
import json
import re
import subprocess

import requests

import config
import git_utils
import interactive
import templates


def token_headers():
    return {"PRIVATE-TOKEN": config.GITLAB_TOKEN}


def get_project_id():
    project_link = git_utils.get_project_link_from_current_dir()
    if project_link == -1:
        return interactive.enter_project_id()

    all_projects = get_all_projects(project_link)
    for project in all_projects or []:
        if project.get("ssh_url_to_repo") == project_link:
            return project.get("id")
    return None


def get_all_projects(project_link):
    project_name = project_link.split("/")[-1].split(".")[0]
    url = f"{config.API_URL}/projects?membership=true&search={project_name}"
    response = requests.get(url, headers=token_headers())

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
        ["glab", "api", f"/groups/{config.GROUP_ID}/milestones?state=active"],
        stdout=subprocess.PIPE,
        text=True,
    )
    milestones = json.loads(result.stdout)
    if current:
        today = datetime.date.today().strftime("%Y-%m-%d")
        active_milestones = [
            milestone
            for milestone in milestones
            if milestone["start_date"] and milestone["due_date"]
            and milestone["start_date"] <= today <= milestone["due_date"]
        ]
        active_milestones.sort(key=lambda item: item["due_date"])
        return active_milestones[0]
    return milestones


def list_iterations():
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.GROUP_ID}/iterations?state=opened"],
        stdout=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def get_active_iteration():
    iterations = list_iterations()
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = [
        iteration
        for iteration in iterations
        if iteration["start_date"] and iteration["due_date"]
        and iteration["start_date"] <= today <= iteration["due_date"]
    ]
    active_iterations.sort(key=lambda item: item["due_date"])
    return active_iterations[0]


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"], text=True)
    return json.loads(output)


def list_epics():
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.GROUP_ID}/epics?per_page=1000&state=opened"],
        stdout=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def create_issue(title, project_id, milestone_id, epic, iteration, settings):
    if not settings:
        print("No settings in template")
        exit(2)

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
    labels = ",".join(labels) if isinstance(labels, list) else labels
    assignee_id = get_authorized_user()["id"]
    issue_command = [
        "glab",
        "api",
        f"/projects/{project_id}/issues",
        "-f",
        f"title={title}",
        "-f",
        f"assignee_ids={assignee_id}",
        "-f",
        f"issue_type={issue_type}",
    ]

    optional_fields = {
        "labels": labels,
        "weight": weight,
        "milestone_id": milestone_id,
    }
    for name, value in optional_fields.items():
        if value:
            issue_command.extend(["-f", f"{name}={value}"])

    if epic:
        issue_command.extend(["-f", f"epic_id={epic['id']}"])

    description = ""
    if iteration:
        description += f"/iteration *iteration:{iteration['id']} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "

    issue_command.extend(["-f", f"description={description}"])
    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_branch(project_id, issue):
    issue_id = str(issue["iid"])
    title = re.sub(r"\s+", "-", issue["title"]).lower()
    title = issue_id + "-" + title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    branch_output = subprocess.check_output(
        [
            "glab",
            "api",
            f"/projects/{project_id}/repository/branches",
            "-f",
            f"branch={title}",
            "-f",
            f"ref={config.MAIN_BRANCH}",
            "-f",
            f"issue_iid={issue_id}",
        ]
    )
    return json.loads(branch_output.decode())


def create_merge_request(project_id, branch, issue, labels, milestone_id):
    issue_id = str(issue["iid"])
    branch_name = branch["name"]
    assignee_id = get_authorized_user()["id"]
    labels = ",".join(labels) if isinstance(labels, list) else labels
    merge_request_command = [
        "glab",
        "api",
        f"/projects/{project_id}/merge_requests",
        "-f",
        f"title={issue['title']}",
        "-f",
        f'description="Closes #{issue_id}"',
        "-f",
        f"source_branch={branch_name}",
        "-f",
        f"target_branch={config.MAIN_BRANCH}",
        "-f",
        f"issue_iid={issue_id}",
        "-f",
        f"assignee_ids={assignee_id}",
    ]

    if config.SQUASH_COMMITS:
        merge_request_command.extend(["-f", "squash=true"])
    if config.DELETE_BRANCH:
        merge_request_command.extend(["-f", "remove_source_branch=true"])
    if labels:
        merge_request_command.extend(["-f", f"labels={labels}"])
    if milestone_id:
        merge_request_command.extend(["-f", f"milestone_id={milestone_id}"])

    merge_request_output = subprocess.check_output(merge_request_command)
    return json.loads(merge_request_output.decode())


def get_merge_request_for_branch(branch_name):
    project_id = get_project_id()
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests"
    params = {"source_branch": branch_name}

    response = requests.get(api_url, headers=token_headers(), params=params)
    if response.status_code == 200:
        for merge_request in response.json():
            if merge_request["source_branch"] == branch_name:
                return merge_request
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def get_active_merge_request_id():
    return get_merge_request_for_branch(git_utils.get_current_branch())["iid"]


def get_current_issue_id():
    merge_request = get_merge_request_for_branch(git_utils.get_current_branch())
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]


def fetch_reviewer_choices():
    reviewer_choices = []
    for reviewer_id in templates.REVIEWERS:
        api_url = f"{config.API_URL}/users/{reviewer_id}"
        try:
            response = requests.get(api_url, headers=token_headers())
            if response.status_code == 200:
                user = response.json()
                reviewer_choices.append((f"{user.get('name')} ({user.get('username')})", reviewer_id))
            else:
                reviewer_choices.append((str(reviewer_id), reviewer_id))
        except Exception:
            reviewer_choices.append((str(reviewer_id), reviewer_id))
    return reviewer_choices


def add_reviewers_to_merge_request(reviewers=None):
    project_id = get_project_id()
    merge_request_id = get_active_merge_request_id()
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests/{merge_request_id}"
    data = {"reviewer_ids": reviewers if reviewers is not None else templates.REVIEWERS}
    requests.put(api_url, headers=token_headers(), json=data)


def set_merge_request_to_auto_merge():
    project_id = get_project_id()
    merge_request_id = get_active_merge_request_id()
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests/{merge_request_id}/merge"
    data = {
        "id": project_id,
        "merge_request_iid": merge_request_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    requests.put(api_url, headers=token_headers(), json=data)


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
            ["glab", "api", f"/groups/{config.GROUP_ID}/labels?search={search}"],
            stdout=subprocess.PIPE,
            check=True,
            text=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as error:
        print(f"Error getting labels: {str(error)}")
        return []
