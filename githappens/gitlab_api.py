"""Small GitLab API wrapper used by the CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class GitLabClient:
    """Typed wrapper around the GitLab HTTP API."""

    api_url: str
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"PRIVATE-TOKEN": self.token}

    def get(self, path: str, **params: Any) -> requests.Response:
        return requests.get(f"{self.api_url}{path}", headers=self.headers, params=params or None)

    def put(self, path: str, json: dict[str, Any] | None = None) -> requests.Response:
        return requests.put(f"{self.api_url}{path}", headers=self.headers, json=json)

    def list_projects(self, project_link: str) -> list[dict[str, Any]] | None:
        response = self.get(
            "/projects",
            membership="true",
            search=project_link.split("/")[-1].split(".")[0],
        )
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
            print("Please generate a new token and update your configs/config.ini.")
            raise SystemExit(1)
        print(f"Request failed with status code {response.status_code}")
        return None
