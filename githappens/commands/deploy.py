from __future__ import annotations

import datetime

from .. import git_utils, interactive
from ..config import AppConfig
from ..gitlab_api import headers


def get_last_production_deploy(config: AppConfig):
    import requests

    try:
        project_id = interactive.get_project_id(config)
        params = {"per_page": 50, "order_by": "updated_at", "sort": "desc"}
        params["ref"] = config.main_branch or _fallback_main_branch()

        response = requests.get(f"{config.api_url}/projects/{project_id}/pipelines", headers=headers(config), params=params)
        if response.status_code != 200:
            print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
            return

        production_pipeline = _find_production_pipeline(config, project_id, response.json())
        if not production_pipeline:
            print("No production deployment found matching pattern")
            return
        _print_production_pipeline(production_pipeline)
    except Exception as e:
        print(f"Error fetching last production deploy: {str(e)}")


def _find_production_pipeline(config: AppConfig, project_id, pipelines):
    import requests

    for pipeline in pipelines:
        detail_response = requests.get(
            f"{config.api_url}/projects/{project_id}/pipelines/{pipeline['id']}/jobs",
            headers=headers(config),
        )
        if detail_response.status_code != 200:
            continue
        for job in detail_response.json():
            if job.get("status", "").lower() != "success":
                continue
            mapping = config.production_mappings.get(str(project_id))
            if mapping:
                expected_stage = mapping.get("stage", "").lower()
                expected_job = mapping.get("job", "").lower()
                if job.get("stage", "").lower() == expected_stage or (
                    expected_job and job.get("name", "").lower() == expected_job
                ):
                    return {"pipeline": pipeline, "production_job": job}
            else:
                print("Didn't find deployment pipeline")
    return None


def _print_production_pipeline(production_pipeline):
    pipeline = production_pipeline["pipeline"]
    job = production_pipeline["production_job"]
    print("🚀 Last Production Deployment:")
    print(f"   Pipeline: #{pipeline['id']} - {pipeline['status']}")
    print(f"   Job: {job['name']} ({job['status']})")
    print(f"   Branch/Tag: {pipeline['ref']}")
    print(f"   Started: {job.get('started_at', 'N/A')}")
    print(f"   Finished: {job.get('finished_at', 'N/A')}")
    print(f"   Duration: {job.get('duration', 'N/A')} seconds" if job.get("duration") else "   Duration: N/A")
    print(f"   Commit: {pipeline['sha'][:8]}")
    print(f"   URL: {pipeline['web_url']}")
    _print_finished_delta(job.get("finished_at"))


def _print_finished_delta(finished_at):
    if not finished_at:
        return
    try:
        finished_time = datetime.datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
        time_diff = datetime.datetime.now(datetime.timezone.utc) - finished_time
        if time_diff.days > 0:
            print(f"   ⏰ {time_diff.days} days ago")
        elif time_diff.seconds > 3600:
            print(f"   ⏰ {time_diff.seconds // 3600} hours ago")
        else:
            print(f"   ⏰ {time_diff.seconds // 60} minutes ago")
    except Exception:
        pass


def _fallback_main_branch():
    try:
        return git_utils.get_main_branch()
    except Exception:
        return "main"
