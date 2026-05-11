from __future__ import annotations

import datetime
from typing import Any

import requests

from ..config import AppConfig
from ..git_utils import get_main_branch
from ..gitlab_api import get_project_id


def _job_matches(config: AppConfig, project_id: str | int, stage: str, job_name: str) -> bool:
    project_mapping = config.production_mappings.get(str(project_id))
    if not project_mapping:
        print("Didn't find deployment pipeline")
        return False

    expected_stage = project_mapping.get("stage", "").lower()
    expected_job = project_mapping.get("job", "").lower()
    return stage.lower() == expected_stage or bool(expected_job and job_name.lower() == expected_job)


def get_last_production_deploy(config: AppConfig) -> dict[str, Any] | None:
    project_id = get_project_id(config)
    params = {"per_page": 50, "order_by": "updated_at", "sort": "desc"}
    params["ref"] = config.main_branch or get_main_branch()

    response = requests.get(
        f"{config.api_url}/projects/{project_id}/pipelines",
        headers={"Private-Token": config.gitlab_token},
        params=params,
    )
    if response.status_code != 200:
        print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
        return None

    for pipeline in response.json():
        detail_response = requests.get(
            f"{config.api_url}/projects/{project_id}/pipelines/{pipeline['id']}/jobs",
            headers={"Private-Token": config.gitlab_token},
        )
        if detail_response.status_code != 200:
            continue

        for job in detail_response.json():
            if job.get("status", "").lower() != "success":
                continue
            if _job_matches(config, project_id, job.get("stage", ""), job.get("name", "")):
                return {"pipeline": pipeline, "production_job": job}
    return None


def print_last_production_deploy(config: AppConfig) -> None:
    production_deploy = get_last_production_deploy(config)
    if not production_deploy:
        print("No production deployment found matching pattern")
        return

    pipeline = production_deploy["pipeline"]
    job = production_deploy["production_job"]
    print("Last Production Deployment:")
    print(f"   Pipeline: #{pipeline['id']} - {pipeline['status']}")
    print(f"   Job: {job['name']} ({job['status']})")
    print(f"   Branch/Tag: {pipeline['ref']}")
    print(f"   Started: {job.get('started_at', 'N/A')}")
    print(f"   Finished: {job.get('finished_at', 'N/A')}")
    print(f"   Duration: {job.get('duration', 'N/A')} seconds" if job.get("duration") else "   Duration: N/A")
    print(f"   Commit: {pipeline['sha'][:8]}")
    print(f"   URL: {pipeline['web_url']}")

    if job.get("finished_at"):
        try:
            finished_time = datetime.datetime.fromisoformat(job["finished_at"].replace("Z", "+00:00"))
            time_diff = datetime.datetime.now(datetime.timezone.utc) - finished_time
            if time_diff.days > 0:
                print(f"   {time_diff.days} days ago")
            elif time_diff.seconds > 3600:
                print(f"   {time_diff.seconds // 3600} hours ago")
            else:
                print(f"   {time_diff.seconds // 60} minutes ago")
        except Exception:
            pass
