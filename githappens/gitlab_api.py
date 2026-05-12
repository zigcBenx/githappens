import json
import subprocess

import requests

from . import git_utils


def private_token_headers(ctx):
    return {"Private-Token": ctx.settings.gitlab_token}


def get_all_projects(ctx, project_link):
    url = (
        f"{ctx.settings.api_url}/projects?membership=true&search="
        f"{project_link.split('/')[-1].split('.')[0]}"
    )
    response = requests.get(url, headers={"PRIVATE-TOKEN": ctx.settings.gitlab_token})

    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        print(
            "Error: Unauthorized (401). Your GitLab token is probably expired, "
            "invalid, or missing required permissions."
        )
        print("Please generate a new token and update your configs/config.ini.")
        raise SystemExit(1)

    print(f"Request failed with status code {response.status_code}")
    return []


def get_project_id(ctx):
    project_link = git_utils.get_project_link_from_current_dir()
    if project_link == -1:
        from .interactive import enter_project_id

        return enter_project_id()

    matching_id = None
    for project in get_all_projects(ctx, project_link):
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def list_milestones(ctx, current=False):
    result = subprocess.run(
        ["glab", "api", f"/groups/{ctx.settings.group_id}/milestones?state=active"],
        stdout=subprocess.PIPE,
        text=True,
    )
    milestones = json.loads(result.stdout)
    if current:
        import datetime

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


def list_iterations(ctx):
    result = subprocess.run(
        ["glab", "api", f"/groups/{ctx.settings.group_id}/iterations?state=opened"],
        stdout=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def list_epics(ctx):
    result = subprocess.run(
        [
            "glab",
            "api",
            f"/groups/{ctx.settings.group_id}/epics?per_page=1000&state=opened",
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    return json.loads(result.stdout)


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def execute_issue_create(
    ctx,
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
        f"/projects/{str(project_id)}/issues",
        "-f",
        f"title={title}",
        "-f",
        f"assignee_ids={assignee_id}",
        "-f",
        f"issue_type={issue_type}",
    ]

    optional_fields = {
        "labels": labels,
        "weight": str(weight) if weight else None,
        "milestone_id": str(milestone_id) if milestone_id else None,
    }

    if epic:
        optional_fields["epic_id"] = str(epic["id"])

    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    optional_fields["description"] = description

    for field, value in optional_fields.items():
        if value:
            issue_command.extend(["-f", f"{field}={value}"])

    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_branch(ctx, project_id, issue):
    issue_id = str(issue["iid"])
    branch_name = git_utils.build_branch_name(issue)
    branch_output = subprocess.check_output(
        [
            "glab",
            "api",
            f"/projects/{str(project_id)}/repository/branches",
            "-f",
            f"branch={branch_name}",
            "-f",
            f"ref={ctx.main_branch}",
            "-f",
            f"issue_iid={issue_id}",
        ]
    )
    return json.loads(branch_output.decode())


def create_merge_request(ctx, project_id, branch, issue, labels, milestone_id):
    issue_id = str(issue["iid"])
    branch_name = branch["name"]
    assignee_id = get_authorized_user()["id"]
    labels = ",".join(labels) if isinstance(labels, list) else labels
    command = [
        "glab",
        "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f",
        f"title={issue['title']}",
        "-f",
        f'description="Closes #{issue_id}"',
        "-f",
        f"source_branch={branch_name}",
        "-f",
        f"target_branch={ctx.main_branch}",
        "-f",
        f"issue_iid={issue_id}",
        "-f",
        f"assignee_ids={assignee_id}",
    ]

    if ctx.settings.squash_commits:
        command.extend(["-f", "squash=true"])
    if ctx.settings.delete_branch_after_merge:
        command.extend(["-f", "remove_source_branch=true"])
    if labels:
        command.extend(["-f", f"labels={labels}"])
    if milestone_id:
        command.extend(["-f", f"milestone_id={str(milestone_id)}"])

    mr_output = subprocess.check_output(command)
    return json.loads(mr_output.decode())


def get_merge_request_for_branch(ctx, branch_name):
    project_id = get_project_id(ctx)
    api_url = f"{ctx.settings.api_url}/projects/{project_id}/merge_requests"
    response = requests.get(
        api_url,
        headers=private_token_headers(ctx),
        params={"source_branch": branch_name},
    )
    if response.status_code == 200:
        for merge_request in response.json():
            if merge_request["source_branch"] == branch_name:
                return merge_request
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def find_merge_request_id_by_branch(ctx, branch_name):
    return get_merge_request_for_branch(ctx, branch_name)["iid"]


def add_reviewers_to_merge_request(ctx, mr_id, reviewers=None):
    project_id = get_project_id(ctx)
    api_url = f"{ctx.settings.api_url}/projects/{project_id}/merge_requests/{mr_id}"
    data = {"reviewer_ids": reviewers if reviewers is not None else ctx.reviewers}
    requests.put(api_url, headers=private_token_headers(ctx), json=data)


def set_merge_request_to_auto_merge(ctx, mr_id):
    project_id = get_project_id(ctx)
    api_url = f"{ctx.settings.api_url}/projects/{project_id}/merge_requests/{mr_id}/merge"
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    requests.put(api_url, headers=private_token_headers(ctx), json=data)


def get_labels_of_group(ctx, search=""):
    try:
        result = subprocess.run(
            ["glab", "api", f"/groups/{ctx.settings.group_id}/labels?search={search}"],
            stdout=subprocess.PIPE,
            check=True,
            text=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as exc:
        print(f"Error getting labels: {str(exc)}")
        return []


def close_opened_issue(project_id, issue_iid):
    command = [
        "glab",
        "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        "-X",
        "PUT",
        "-f",
        "state_event=close",
    ]
    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        print(f"Error closing issue: {str(exc)}")


def get_pipelines(ctx, project_id, params):
    response = requests.get(
        f"{ctx.settings.api_url}/projects/{project_id}/pipelines",
        headers=private_token_headers(ctx),
        params=params,
    )
    return response


def get_pipeline_jobs(ctx, project_id, pipeline_id):
    return requests.get(
        f"{ctx.settings.api_url}/projects/{project_id}/pipelines/{pipeline_id}/jobs",
        headers=private_token_headers(ctx),
    )
