from __future__ import annotations

import json
import subprocess
from typing import Any

from .config import AppConfig


def headers(config: AppConfig) -> dict[str, str]:
    return {"PRIVATE-TOKEN": config.gitlab_token}


def get_all_projects(config: AppConfig, project_link: str) -> list[dict[str, Any]] | None:
    import requests

    url = f"{config.api_url}/projects?membership=true&search={project_link.split('/')[-1].split('.')[0]}"
    response = requests.get(url, headers=headers(config))
    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        raise SystemExit(1)
    print(f"Request failed with status code {response.status_code}")
    return None


def list_milestones(config: AppConfig) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.group_id}/milestones?state=active"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def list_iterations(config: AppConfig) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.group_id}/iterations?state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def list_epics(config: AppConfig) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.group_id}/epics?per_page=1000&state=opened"],
        stdout=subprocess.PIPE,
    )
    return json.loads(result.stdout)


def get_authorized_user() -> dict[str, Any]:
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def execute_issue_create(
    config: AppConfig,
    project_id,
    title: str,
    labels,
    milestone_id,
    epic,
    iteration,
    weight,
    estimated_time,
    issue_type: str = "issue",
) -> dict[str, Any]:
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
    _append_field(issue_command, "labels", labels)
    _append_field(issue_command, "weight", str(weight) if weight else None)
    _append_field(issue_command, "milestone_id", str(milestone_id) if milestone_id else None)
    _append_field(issue_command, "epic_id", str(epic["id"]) if epic else None)

    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    _append_field(issue_command, "description", description)

    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_branch(config: AppConfig, project_id, issue: dict[str, Any]) -> dict[str, Any]:
    issue_id = str(issue["iid"])
    title = _slugify_branch_title(issue["title"])
    branch = f"{issue_id}-{title}"
    branch_output = subprocess.check_output(
        [
            "glab",
            "api",
            f"/projects/{str(project_id)}/repository/branches",
            "-f",
            f"branch={branch}",
            "-f",
            f"ref={config.main_branch}",
            "-f",
            f"issue_iid={issue_id}",
        ]
    )
    return json.loads(branch_output.decode())


def create_merge_request(config: AppConfig, project_id, branch, issue, labels, milestone_id):
    issue_id = str(issue["iid"])
    branch_name = branch["name"]
    labels = ",".join(labels) if isinstance(labels, list) else labels
    assignee_id = get_authorized_user()["id"]
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
        f"target_branch={config.main_branch}",
        "-f",
        f"issue_iid={issue_id}",
        "-f",
        f"assignee_ids={assignee_id}",
    ]
    if config.squash_commits:
        _append_field(command, "squash", "true")
    if config.delete_branch:
        _append_field(command, "remove_source_branch", "true")
    _append_field(command, "labels", labels)
    _append_field(command, "milestone_id", str(milestone_id) if milestone_id else None)
    mr_output = subprocess.check_output(command)
    return json.loads(mr_output.decode())


def get_merge_request_for_branch(config: AppConfig, project_id, branch_name: str):
    import requests

    response = requests.get(
        f"{config.api_url}/projects/{project_id}/merge_requests",
        headers=headers(config),
        params={"source_branch": branch_name},
    )
    if response.status_code == 200:
        for mr in response.json():
            if mr["source_branch"] == branch_name:
                return mr
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def add_reviewers_to_merge_request(config: AppConfig, project_id, mr_id, reviewers=None) -> None:
    import requests

    requests.put(
        f"{config.api_url}/projects/{project_id}/merge_requests/{mr_id}",
        headers=headers(config),
        json={"reviewer_ids": reviewers if reviewers is not None else config.reviewers},
    )


def set_merge_request_to_auto_merge(config: AppConfig, project_id, mr_id) -> None:
    import requests

    requests.put(
        f"{config.api_url}/projects/{project_id}/merge_requests/{mr_id}/merge",
        headers=headers(config),
        json={
            "id": project_id,
            "merge_request_iid": mr_id,
            "should_remove_source_branch": True,
            "merge_when_pipeline_succeeds": True,
            "auto_merge_strategy": "merge_when_pipeline_succeeds",
        },
    )


def list_group_labels(config: AppConfig, search: str = "") -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["glab", "api", f"/groups/{config.group_id}/labels?search={search}"],
            stdout=subprocess.PIPE,
            check=True,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []


def add_issue_note(project_id, issue_id, body: str) -> None:
    subprocess.run(
        ["glab", "api", f"/projects/{project_id}/issues/{issue_id}/notes", "-f", f"body={body}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def add_spent_time(project_id, issue_id, minutes: int) -> None:
    subprocess.run(
        ["glab", "api", f"/projects/{project_id}/issues/{issue_id}/add_spent_time", "-f", f"duration={minutes}m"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def close_issue(project_id, issue_iid) -> None:
    subprocess.run(
        ["glab", "api", f"/projects/{project_id}/issues/{issue_iid}", "-X", "PUT", "-f", "state_event=close"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _append_field(command: list[str], key: str, value) -> None:
    if value:
        command.extend(["-f", f"{key}={value}"])


def _slugify_branch_title(title: str) -> str:
    import re

    title = re.sub(r"\s+", "-", title).lower()
    return title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
