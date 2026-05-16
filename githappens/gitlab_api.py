from __future__ import annotations

import datetime
import json
import subprocess
from typing import Any

import requests

from .config import AppConfig
from .git_utils import branch_name_for_issue, get_project_link_from_current_dir
from .interactive import (
    enter_project_id,
    get_selected_epic,
    get_selected_iteration,
    get_selected_milestone,
    select_epic,
    select_iteration,
    select_milestone,
)


def _headers(config: AppConfig) -> dict[str, str]:
    return {"PRIVATE-TOKEN": config.gitlab_token, "Private-Token": config.gitlab_token}


def normalize_labels(labels: list[str] | str | None) -> str | None:
    if isinstance(labels, list):
        return ",".join(labels)
    return labels


def get_project_id(config: AppConfig) -> str | int | None:
    project_link = get_project_link_from_current_dir()
    if project_link == -1:
        return enter_project_id()

    all_projects = get_all_projects(config, str(project_link))
    matching_id = None
    for project in all_projects or []:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def get_all_projects(config: AppConfig, project_link: str) -> list[dict[str, Any]] | None:
    url = f"{config.api_url}/projects?membership=true&search={project_link.split('/')[-1].split('.')[0]}"
    response = requests.get(url, headers=_headers(config))
    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        raise SystemExit(1)
    print(f"Request failed with status code {response.status_code}")
    return None


def list_milestones(config: AppConfig, current: bool = False) -> list[dict[str, Any]] | dict[str, Any]:
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.group_id}/milestones?state=active"],
        stdout=subprocess.PIPE,
        check=False,
    )
    milestones = json.loads(result.stdout)
    if current:
        today = datetime.date.today().strftime("%Y-%m-%d")
        active_milestones = [
            milestone
            for milestone in milestones
            if milestone["start_date"] and milestone["due_date"] and milestone["start_date"] <= today <= milestone["due_date"]
        ]
        active_milestones.sort(key=lambda item: item["due_date"])
        return active_milestones[0]
    return milestones


def get_milestone(config: AppConfig, manual: bool) -> dict[str, Any]:
    if manual:
        milestones = list_milestones(config)
        return get_selected_milestone(select_milestone(milestones), milestones)
    return list_milestones(config, True)


def list_iterations(config: AppConfig) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.group_id}/iterations?state=opened"],
        stdout=subprocess.PIPE,
        check=False,
    )
    return json.loads(result.stdout)


def get_active_iteration(config: AppConfig) -> dict[str, Any]:
    iterations = list_iterations(config)
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = [
        iteration
        for iteration in iterations
        if iteration["start_date"] and iteration["due_date"] and iteration["start_date"] <= today <= iteration["due_date"]
    ]
    active_iterations.sort(key=lambda item: item["due_date"])
    return active_iterations[0]


def get_iteration(config: AppConfig, manual: bool) -> dict[str, Any]:
    if manual:
        iterations = list_iterations(config)
        return get_selected_iteration(select_iteration(iterations), iterations)
    return get_active_iteration(config)


def list_epics(config: AppConfig) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["glab", "api", f"/groups/{config.group_id}/epics?per_page=1000&state=opened"],
        stdout=subprocess.PIPE,
        check=False,
    )
    return json.loads(result.stdout)


def get_epic(config: AppConfig) -> dict[str, Any]:
    epics = list_epics(config)
    return get_selected_epic(select_epic(epics), epics)


def get_authorized_user() -> dict[str, Any]:
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def get_user_details(config: AppConfig, reviewer_id: int) -> dict[str, Any] | None:
    try:
        response = requests.get(f"{config.api_url}/users/{reviewer_id}", headers=_headers(config))
    except Exception:
        return None
    if response.status_code != 200:
        return None
    return response.json()


def build_issue_description(iteration: dict[str, Any] | bool, estimated_time: str | int | None) -> str:
    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    return description


def execute_issue_create(
    config: AppConfig,
    project_id: str | int,
    title: str,
    labels: list[str] | str | None,
    milestone_id: str | int | bool,
    epic: dict[str, Any] | bool,
    iteration: dict[str, Any] | bool,
    weight: int | None,
    estimated_time: str | int | None,
    issue_type: str = "issue",
) -> dict[str, Any]:
    label_value = normalize_labels(labels)
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
    if label_value:
        issue_command.extend(["-f", f"labels={label_value}"])
    if weight:
        issue_command.extend(["-f", f"weight={str(weight)}"])
    if milestone_id:
        issue_command.extend(["-f", f"milestone_id={str(milestone_id)}"])
    if epic:
        issue_command.extend(["-f", f"epic_id={str(epic['id'])}"])
    issue_command.extend(["-f", f"description={build_issue_description(iteration, estimated_time)}"])
    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_issue(
    config: AppConfig,
    title: str,
    project_id: str | int,
    milestone_id: str | int | bool,
    epic: dict[str, Any] | bool,
    iteration: dict[str, Any] | bool,
    settings: dict[str, Any],
) -> dict[str, Any]:
    if not settings:
        print("No settings in template")
        raise SystemExit(2)

    issue_type = settings.get("type") or "issue"
    return execute_issue_create(
        config,
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


def create_branch(config: AppConfig, project_id: str | int, issue: dict[str, Any]) -> dict[str, Any]:
    branch_output = subprocess.check_output(
        [
            "glab",
            "api",
            f"/projects/{str(project_id)}/repository/branches",
            "-f",
            f"branch={branch_name_for_issue(issue)}",
            "-f",
            f"ref={config.main_branch}",
            "-f",
            f"issue_iid={str(issue['iid'])}",
        ]
    )
    return json.loads(branch_output.decode())


def create_merge_request(
    config: AppConfig,
    project_id: str | int,
    branch: dict[str, Any],
    issue: dict[str, Any],
    labels: list[str] | str | None,
    milestone_id: str | int | bool,
) -> dict[str, Any]:
    issue_id = str(issue["iid"])
    label_value = normalize_labels(labels)
    assignee_id = get_authorized_user()["id"]
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
        f"target_branch={config.main_branch}",
        "-f",
        f"issue_iid={issue_id}",
        "-f",
        f"assignee_ids={assignee_id}",
    ]
    if config.squash_commits:
        merge_request_command.extend(["-f", "squash=true"])
    if config.delete_branch:
        merge_request_command.extend(["-f", "remove_source_branch=true"])
    if label_value:
        merge_request_command.extend(["-f", f"labels={label_value}"])
    if milestone_id:
        merge_request_command.extend(["-f", f"milestone_id={str(milestone_id)}"])

    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())


def get_merge_request_for_branch(config: AppConfig, branch_name: str) -> dict[str, Any] | None:
    project_id = get_project_id(config)
    response = requests.get(
        f"{config.api_url}/projects/{project_id}/merge_requests",
        headers=_headers(config),
        params={"source_branch": branch_name},
    )
    if response.status_code == 200:
        for merge_request in response.json():
            if merge_request["source_branch"] == branch_name:
                return merge_request
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def find_merge_request_id_by_branch(config: AppConfig, branch_name: str) -> int:
    return get_merge_request_for_branch(config, branch_name)["iid"]


def add_reviewers_to_merge_request(config: AppConfig, reviewers: list[int] | None = None) -> None:
    from .git_utils import get_current_branch

    project_id = get_project_id(config)
    mr_id = find_merge_request_id_by_branch(config, get_current_branch())
    requests.put(
        f"{config.api_url}/projects/{project_id}/merge_requests/{mr_id}",
        headers=_headers(config),
        json={"reviewer_ids": reviewers if reviewers is not None else config.reviewers},
    )


def set_merge_request_to_auto_merge(config: AppConfig) -> None:
    from .git_utils import get_current_branch

    project_id = get_project_id(config)
    mr_id = find_merge_request_id_by_branch(config, get_current_branch())
    requests.put(
        f"{config.api_url}/projects/{project_id}/merge_requests/{mr_id}/merge",
        headers=_headers(config),
        json={
            "id": project_id,
            "merge_request_iid": mr_id,
            "should_remove_source_branch": True,
            "merge_when_pipeline_succeeds": True,
            "auto_merge_strategy": "merge_when_pipeline_succeeds",
        },
    )


def get_current_issue_id(config: AppConfig) -> str:
    from .git_utils import get_current_branch

    merge_request = get_merge_request_for_branch(config, get_current_branch())
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time(config: AppConfig) -> None:
    import inquirer

    try:
        project_id = get_project_id(config)
        issue_id = get_current_issue_id(config)
    except Exception as error:
        print(f"Error getting issue details: {str(error)}")
        return

    spent_time = inquirer.prompt(
        [
            inquirer.Text(
                "spent_time",
                message="How many minutes did you actually spend on this issue?",
                validate=lambda _, value: value.isdigit(),
            )
        ]
    )["spent_time"]

    try:
        subprocess.run(
            [
                "glab",
                "api",
                f"/projects/{project_id}/issues/{issue_id}/notes",
                "-f",
                f"body=/spend {spent_time}m",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except subprocess.CalledProcessError as error:
        print(f"Error adding time tracking: {str(error)}")
    except Exception as error:
        print(f"Error tracking issue: {str(error)}")


def close_opened_issue(config: AppConfig, issue_iid: str | int, project_id: str | int) -> None:
    subprocess.run(
        [
            "glab",
            "api",
            f"/projects/{project_id}/issues/{issue_iid}",
            "-X",
            "PUT",
            "-f",
            "state_event=close",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def get_labels_of_group(config: AppConfig, search: str = "") -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["glab", "api", f"/groups/{config.group_id}/labels?search={search}"],
            stdout=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        print(f"Error getting labels: {str(error)}")
        return []
    return json.loads(result.stdout)


def add_spent_time(project_id: str | int, issue_id: str | int, minutes: str | int) -> None:
    subprocess.run(
        [
            "glab",
            "api",
            f"/projects/{project_id}/issues/{issue_id}/add_spent_time",
            "-f",
            f"duration={minutes}m",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
