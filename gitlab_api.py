import datetime
import json
import subprocess
from typing import Any, Dict, Iterable, List, Optional

import requests


class GitLabAPI:
    def __init__(self, settings, http_client=None):
        self.settings = settings
        self.http = http_client or requests

    @property
    def headers(self) -> Dict[str, str]:
        return {"Private-Token": self.settings.gitlab_token}

    def get_all_projects(self, project_link):
        search_term = project_link.split("/")[-1].split(".")[0]
        response = self.http.get(
            f"{self.settings.api_url}/projects",
            headers=self.headers,
            params={"membership": "true", "search": search_term},
        )

        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
            print("Please generate a new token and update your configs/config.ini.")
            raise SystemExit(1)

        print(f"Request failed with status code {response.status_code}")
        return None

    def get_user(self, user_id):
        response = self.http.get(
            f"{self.settings.api_url}/users/{user_id}",
            headers=self.headers,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch user {user_id}: {response.status_code}")
        return response.json()

    def _glab_json(self, path: str) -> Any:
        result = subprocess.run(["glab", "api", path], stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)

    def list_milestones(self, current: bool = False):
        milestones = self._glab_json(f"/groups/{self.settings.group_id}/milestones?state=active")
        if not current:
            return milestones

        today = datetime.date.today().strftime("%Y-%m-%d")
        active_milestones = [
            milestone
            for milestone in milestones
            if milestone["start_date"] and milestone["due_date"]
            and milestone["start_date"] <= today <= milestone["due_date"]
        ]
        active_milestones.sort(key=lambda milestone: milestone["due_date"])
        return active_milestones[0]

    def list_iterations(self):
        return self._glab_json(f"/groups/{self.settings.group_id}/iterations?state=opened")

    def get_active_iteration(self):
        iterations = self.list_iterations()
        today = datetime.date.today().strftime("%Y-%m-%d")
        active_iterations = [
            iteration
            for iteration in iterations
            if iteration["start_date"] and iteration["due_date"]
            and iteration["start_date"] <= today <= iteration["due_date"]
        ]
        active_iterations.sort(key=lambda iteration: iteration["due_date"])
        return active_iterations[0]

    def get_authorized_user(self):
        output = subprocess.check_output(["glab", "api", "/user"])
        return json.loads(output)

    def list_epics(self):
        return self._glab_json(f"/groups/{self.settings.group_id}/epics?per_page=1000&state=opened")

    def get_labels_of_group(self, search: str = ""):
        try:
            return self._glab_json(f"/groups/{self.settings.group_id}/labels?search={search}")
        except subprocess.CalledProcessError as error:
            print(f"Error getting labels: {str(error)}")
            return []

    def create_issue(
        self,
        project_id,
        title,
        labels,
        milestone_id,
        epic,
        iteration,
        weight,
        estimated_time,
        issue_type: str = "issue",
    ):
        labels = ",".join(labels) if type(labels) == list else labels
        assignee_id = self.get_authorized_user()["id"]
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

    def create_branch(self, project_id, issue, main_branch):
        issue_id = str(issue["iid"])
        title = " ".join(issue["title"].split()).lower()
        title = issue_id + "-" + title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
        branch_output = subprocess.check_output(
            [
                "glab",
                "api",
                f"/projects/{str(project_id)}/repository/branches",
                "-f",
                f"branch={title}",
                "-f",
                f"ref={main_branch}",
                "-f",
                f"issue_iid={issue_id}",
            ]
        )
        return json.loads(branch_output.decode())

    def create_merge_request(self, project_id, branch, issue, labels, milestone_id, main_branch):
        issue_id = str(issue["iid"])
        branch_name = branch["name"]
        labels = ",".join(labels) if type(labels) == list else labels
        assignee_id = self.get_authorized_user()["id"]
        merge_request_command = [
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
            f"target_branch={main_branch}",
            "-f",
            f"issue_iid={issue_id}",
            "-f",
            f"assignee_ids={assignee_id}",
        ]

        if self.settings.squash_commits:
            merge_request_command.extend(["-f", "squash=true"])
        if self.settings.delete_branch:
            merge_request_command.extend(["-f", "remove_source_branch=true"])
        if labels:
            merge_request_command.extend(["-f", f"labels={labels}"])
        if milestone_id:
            merge_request_command.extend(["-f", f"milestone_id={str(milestone_id)}"])

        mr_output = subprocess.check_output(merge_request_command)
        return json.loads(mr_output.decode())

    def get_merge_request_for_branch(self, project_id, branch_name):
        response = self.http.get(
            f"{self.settings.api_url}/projects/{project_id}/merge_requests",
            headers=self.headers,
            params={"source_branch": branch_name},
        )
        if response.status_code == 200:
            for merge_request in response.json():
                if merge_request["source_branch"] == branch_name:
                    return merge_request
        else:
            print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
        return None

    def add_reviewers_to_merge_request(self, project_id, mr_id, reviewers: Optional[Iterable[int]] = None):
        data = {"reviewer_ids": reviewers if reviewers is not None else self.settings.reviewers}
        self.http.put(
            f"{self.settings.api_url}/projects/{project_id}/merge_requests/{mr_id}",
            headers=self.headers,
            json=data,
        )

    def set_merge_request_to_auto_merge(self, project_id, mr_id):
        data = {
            "id": project_id,
            "merge_request_iid": mr_id,
            "should_remove_source_branch": True,
            "merge_when_pipeline_succeeds": True,
            "auto_merge_strategy": "merge_when_pipeline_succeeds",
        }
        self.http.put(
            f"{self.settings.api_url}/projects/{project_id}/merge_requests/{mr_id}/merge",
            headers=self.headers,
            json=data,
        )

    def close_opened_issue(self, issue_iid, project_id):
        try:
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
            )
        except subprocess.CalledProcessError as error:
            print(f"Error closing issue: {str(error)}")

    def add_spent_time(self, project_id, issue_id, minutes):
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
        )

    def add_time_tracking_note(self, project_id, issue_id, spent_time):
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

    def list_pipelines(self, project_id, ref):
        response = self.http.get(
            f"{self.settings.api_url}/projects/{project_id}/pipelines",
            headers=self.headers,
            params={"per_page": 50, "order_by": "updated_at", "sort": "desc", "ref": ref},
        )
        return response

    def list_pipeline_jobs(self, project_id, pipeline_id):
        return self.http.get(
            f"{self.settings.api_url}/projects/{project_id}/pipelines/{pipeline_id}/jobs",
            headers=self.headers,
        )
