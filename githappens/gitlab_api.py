from __future__ import annotations

import json
import subprocess

from githappens.git_utils import build_branch_name


class GitLabApiError(RuntimeError):
    """Raised when a GitLab API request fails."""


class GitLabClient:
    def __init__(self, base_url: str, api_url: str, group_id: str, gitlab_token: str):
        self.base_url = base_url.rstrip("/")
        self.api_url = api_url.rstrip("/")
        self.group_id = group_id
        self.gitlab_token = gitlab_token

    @classmethod
    def from_config(cls, config) -> "GitLabClient":
        return cls(config.base_url, config.api_url, config.group_id, config.gitlab_token)

    def _headers(self) -> dict[str, str]:
        return {"Private-Token": self.gitlab_token}

    def _request(self, method: str, path: str, **kwargs):
        import requests

        response = requests.request(
            method,
            f"{self.api_url}{path}",
            headers=self._headers(),
            **kwargs,
        )

        if response.status_code == 401:
            raise GitLabApiError(
                "Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions."
            )

        if not response.ok:
            raise GitLabApiError(f"Request failed with status code {response.status_code}: {response.text}")

        return response

    def _glab_json(self, *args: str) -> dict | list:
        try:
            output = subprocess.check_output(["glab", "api", *args], text=True)
        except subprocess.CalledProcessError as exc:
            raise GitLabApiError(exc.output.strip() or str(exc)) from exc
        return json.loads(output)

    def _glab_run(self, *args: str) -> None:
        try:
            subprocess.run(
                ["glab", "api", *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise GitLabApiError(exc.stderr.strip() or exc.stdout.strip() or str(exc)) from exc

    def get_all_projects(self, search_term: str) -> list[dict]:
        response = self._request(
            "GET",
            "/projects",
            params={"membership": "true", "search": search_term},
        )
        return response.json()

    def list_milestones(self) -> list[dict]:
        return self._glab_json(f"/groups/{self.group_id}/milestones?state=active")

    def list_iterations(self) -> list[dict]:
        return self._glab_json(f"/groups/{self.group_id}/iterations?state=opened")

    def list_epics(self) -> list[dict]:
        return self._glab_json(f"/groups/{self.group_id}/epics?per_page=1000&state=opened")

    def get_authorized_user(self) -> dict:
        return self._glab_json("/user")

    def create_issue(
        self,
        project_id: int | str,
        title: str,
        labels,
        milestone_id,
        epic,
        iteration,
        weight,
        estimated_time,
        issue_type: str = "issue",
    ) -> dict:
        labels_value = ",".join(labels) if isinstance(labels, list) else labels
        assignee_id = self.get_authorized_user()["id"]
        description = ""

        if iteration:
            description += f"/iteration *iteration:{iteration['id']} "

        if estimated_time:
            description += f"\n/estimate {estimated_time}m "

        args = [
            f"/projects/{project_id}/issues",
            "-f",
            f"title={title}",
            "-f",
            f"assignee_ids={assignee_id}",
            "-f",
            f"issue_type={issue_type}",
            "-f",
            f"description={description}",
        ]

        if labels_value:
            args.extend(["-f", f"labels={labels_value}"])
        if weight:
            args.extend(["-f", f"weight={weight}"])
        if milestone_id:
            args.extend(["-f", f"milestone_id={milestone_id}"])
        if epic:
            args.extend(["-f", f"epic_id={epic['id']}"])

        return self._glab_json(*args)

    def create_branch(self, project_id: int | str, issue: dict, main_branch: str) -> dict:
        branch_name = build_branch_name(issue["iid"], issue["title"])
        return self._glab_json(
            f"/projects/{project_id}/repository/branches",
            "-f",
            f"branch={branch_name}",
            "-f",
            f"ref={main_branch}",
            "-f",
            f"issue_iid={issue['iid']}",
        )

    def create_merge_request(
        self,
        project_id: int | str,
        branch: dict,
        issue: dict,
        labels,
        milestone_id,
        main_branch: str,
        squash_commits: bool,
        delete_branch_after_merge: bool,
    ) -> dict:
        labels_value = ",".join(labels) if isinstance(labels, list) else labels
        assignee_id = self.get_authorized_user()["id"]
        args = [
            f"/projects/{project_id}/merge_requests",
            "-f",
            f"title={issue['title']}",
            "-f",
            f'description="Closes #{issue["iid"]}"',
            "-f",
            f"source_branch={branch['name']}",
            "-f",
            f"target_branch={main_branch}",
            "-f",
            f"issue_iid={issue['iid']}",
            "-f",
            f"assignee_ids={assignee_id}",
        ]

        if squash_commits:
            args.extend(["-f", "squash=true"])
        if delete_branch_after_merge:
            args.extend(["-f", "remove_source_branch=true"])
        if labels_value:
            args.extend(["-f", f"labels={labels_value}"])
        if milestone_id:
            args.extend(["-f", f"milestone_id={milestone_id}"])

        return self._glab_json(*args)

    def get_merge_request_for_branch(self, project_id: int | str, branch_name: str) -> dict | None:
        response = self._request(
            "GET",
            f"/projects/{project_id}/merge_requests",
            params={"source_branch": branch_name},
        )
        merge_requests = response.json()
        return next((mr for mr in merge_requests if mr["source_branch"] == branch_name), None)

    def get_user(self, user_id: int) -> dict:
        response = self._request("GET", f"/users/{user_id}")
        return response.json()

    def update_merge_request_reviewers(
        self, project_id: int | str, merge_request_id: int | str, reviewer_ids: list[int]
    ) -> None:
        self._request(
            "PUT",
            f"/projects/{project_id}/merge_requests/{merge_request_id}",
            json={"reviewer_ids": reviewer_ids},
        )

    def enable_auto_merge(self, project_id: int | str, merge_request_id: int | str) -> None:
        self._request(
            "PUT",
            f"/projects/{project_id}/merge_requests/{merge_request_id}/merge",
            json={
                "id": project_id,
                "merge_request_iid": merge_request_id,
                "should_remove_source_branch": True,
                "merge_when_pipeline_succeeds": True,
                "auto_merge_strategy": "merge_when_pipeline_succeeds",
            },
        )

    def close_issue(self, project_id: int | str, issue_iid: int | str) -> None:
        self._glab_run(
            f"/projects/{project_id}/issues/{issue_iid}",
            "-X",
            "PUT",
            "-f",
            "state_event=close",
        )

    def list_group_labels(self, search: str = "") -> list[dict]:
        return self._glab_json(f"/groups/{self.group_id}/labels?search={search}")

    def add_issue_note(self, project_id: int | str, issue_iid: int | str, body: str) -> None:
        self._glab_run(
            f"/projects/{project_id}/issues/{issue_iid}/notes",
            "-f",
            f"body={body}",
        )

    def add_issue_spent_time(self, project_id: int | str, issue_iid: int | str, minutes: int) -> None:
        self._glab_run(
            f"/projects/{project_id}/issues/{issue_iid}/add_spent_time",
            "-f",
            f"duration={minutes}m",
        )

    def get_pipeline_jobs(self, project_id: int | str, pipeline_id: int | str) -> list[dict]:
        response = self._request("GET", f"/projects/{project_id}/pipelines/{pipeline_id}/jobs")
        return response.json()

    def get_pipelines(
        self,
        project_id: int | str,
        *,
        per_page: int = 50,
        order_by: str = "updated_at",
        sort: str = "desc",
        ref: str | None = None,
    ) -> list[dict]:
        params = {"per_page": per_page, "order_by": order_by, "sort": sort}
        if ref:
            params["ref"] = ref

        response = self._request("GET", f"/projects/{project_id}/pipelines", params=params)
        return response.json()
