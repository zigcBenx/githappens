from __future__ import annotations

import json
import subprocess
from typing import Any

import requests

from .config import AppConfig

DEFAULT_TIMEOUT_SECONDS = 15


class GitLabApi:
    def __init__(self, config: AppConfig):
        self.config = config

    @property
    def headers(self) -> dict[str, str]:
        return {"PRIVATE-TOKEN": self.config.gitlab_token, "Private-Token": self.config.gitlab_token}

    def get_json(self, path: str, **params: Any) -> Any:
        try:
            response = requests.get(f"{self.config.api_url}{path}", headers=self.headers, params=params or None, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException as error:
            print(f"Request failed: {error}")
            raise SystemExit(1) from error
        if response.status_code == 401:
            print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
            print("Please generate a new token and update your configs/config.ini.")
            raise SystemExit(1)
        if response.status_code != 200:
            print(f"Request failed with status code {response.status_code}")
            return None
        return response.json()

    def put_json(self, path: str, payload: dict[str, Any]) -> requests.Response:
        try:
            return requests.put(f"{self.config.api_url}{path}", headers=self.headers, json=payload, timeout=DEFAULT_TIMEOUT_SECONDS)
        except requests.RequestException as error:
            print(f"Request failed: {error}")
            raise SystemExit(1) from error

    def glab_json(self, args: list[str]) -> Any:
        output = subprocess.check_output(["glab", "api", *args])
        return json.loads(output.decode())

    def glab_run(self, args: list[str]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(["glab", "api", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def get_all_projects(self, project_link: str) -> list[dict[str, Any]]:
        search = project_link.split("/")[-1].split(".")[0]
        return self.get_json("/projects", membership="true", search=search) or []

    def get_authorized_user(self) -> dict[str, Any]:
        return self.glab_json(["/user"])

    def list_group_milestones(self) -> list[dict[str, Any]]:
        return self.glab_json([f"/groups/{self.config.group_id}/milestones?state=active"])

    def list_group_iterations(self) -> list[dict[str, Any]]:
        return self.glab_json([f"/groups/{self.config.group_id}/iterations?state=opened"])

    def list_group_epics(self) -> list[dict[str, Any]]:
        return self.glab_json([f"/groups/{self.config.group_id}/epics?per_page=1000&state=opened"])

    def list_group_labels(self, search: str = "") -> list[dict[str, Any]]:
        try:
            return self.glab_json([f"/groups/{self.config.group_id}/labels?search={search}"])
        except subprocess.CalledProcessError as error:
            print(f"Error getting labels: {error}")
            return []

    def create_issue(
        self,
        project_id: str | int,
        title: str,
        labels: list[str] | str | None,
        milestone_id: int | str | bool | None,
        epic: dict[str, Any] | bool | None,
        iteration: dict[str, Any] | bool | None,
        weight: int | None,
        estimated_time: int | None,
        issue_type: str = "issue",
    ) -> dict[str, Any]:
        label_value = ",".join(labels) if isinstance(labels, list) else labels
        assignee_id = self.get_authorized_user()["id"]
        command = [
            f"/projects/{project_id}/issues",
            "-f",
            f"title={title}",
            "-f",
            f"assignee_ids={assignee_id}",
            "-f",
            f"issue_type={issue_type}",
        ]
        if label_value:
            command.extend(["-f", f"labels={label_value}"])
        if weight:
            command.extend(["-f", f"weight={weight}"])
        if milestone_id:
            command.extend(["-f", f"milestone_id={milestone_id}"])
        if epic:
            command.extend(["-f", f"epic_id={epic['id']}"])

        description = ""
        if iteration:
            description += f"/iteration *iteration:{iteration['id']} "
        if estimated_time:
            description += f"\n/estimate {estimated_time}m "
        command.extend(["-f", f"description={description}"])
        return self.glab_json(command)

    def create_branch(self, project_id: str | int, branch_name: str, issue_iid: str | int, main_branch: str) -> dict[str, Any]:
        return self.glab_json(
            [
                f"/projects/{project_id}/repository/branches",
                "-f",
                f"branch={branch_name}",
                "-f",
                f"ref={main_branch}",
                "-f",
                f"issue_iid={issue_iid}",
            ]
        )

    def create_merge_request(
        self,
        project_id: str | int,
        branch_name: str,
        issue: dict[str, Any],
        labels: list[str] | str | None,
        milestone_id: int | str | bool | None,
        main_branch: str,
    ) -> dict[str, Any]:
        issue_iid = str(issue["iid"])
        label_value = ",".join(labels) if isinstance(labels, list) else labels
        assignee_id = self.get_authorized_user()["id"]
        command = [
            f"/projects/{project_id}/merge_requests",
            "-f",
            f"title={issue['title']}",
            "-f",
            f'description="Closes #{issue_iid}"',
            "-f",
            f"source_branch={branch_name}",
            "-f",
            f"target_branch={main_branch}",
            "-f",
            f"issue_iid={issue_iid}",
            "-f",
            f"assignee_ids={assignee_id}",
        ]
        if self.config.squash_commits:
            command.extend(["-f", "squash=true"])
        if self.config.delete_branch_after_merge:
            command.extend(["-f", "remove_source_branch=true"])
        if label_value:
            command.extend(["-f", f"labels={label_value}"])
        if milestone_id:
            command.extend(["-f", f"milestone_id={milestone_id}"])
        return self.glab_json(command)

    def get_merge_requests_for_branch(self, project_id: str | int, branch_name: str) -> list[dict[str, Any]]:
        return self.get_json(f"/projects/{project_id}/merge_requests", source_branch=branch_name) or []

    def get_user(self, reviewer_id: int) -> dict[str, Any] | None:
        return self.get_json(f"/users/{reviewer_id}")

    def update_merge_request_reviewers(self, project_id: str | int, mr_id: str | int, reviewer_ids: list[int]) -> None:
        self.put_json(f"/projects/{project_id}/merge_requests/{mr_id}", {"reviewer_ids": reviewer_ids})

    def set_merge_request_auto_merge(self, project_id: str | int, mr_id: str | int) -> None:
        self.put_json(
            f"/projects/{project_id}/merge_requests/{mr_id}/merge",
            {
                "id": project_id,
                "merge_request_iid": mr_id,
                "should_remove_source_branch": True,
                "merge_when_pipeline_succeeds": True,
                "auto_merge_strategy": "merge_when_pipeline_succeeds",
            },
        )

    def close_issue(self, project_id: str | int, issue_iid: str | int) -> None:
        self.glab_run([f"/projects/{project_id}/issues/{issue_iid}", "-X", "PUT", "-f", "state_event=close"])

    def add_issue_note(self, project_id: str | int, issue_iid: str | int, body: str) -> subprocess.CompletedProcess[bytes]:
        return self.glab_run([f"/projects/{project_id}/issues/{issue_iid}/notes", "-f", f"body={body}"])

    def add_spent_time(self, project_id: str | int, issue_iid: str | int, minutes: int) -> subprocess.CompletedProcess[bytes]:
        return self.glab_run([f"/projects/{project_id}/issues/{issue_iid}/add_spent_time", "-f", f"duration={minutes}m"])
