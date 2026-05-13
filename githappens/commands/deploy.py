from __future__ import annotations

import datetime

from githappens import git_utils
from githappens.config import AppConfig
from githappens.gitlab_api import GitLabApi
from githappens.commands.create_issue import resolve_project_id


def get_last_production_deploy(config: AppConfig, api: GitLabApi, main_branch: str | None = None) -> None:
    try:
        project_id = resolve_project_id(api)
        ref = config.production_ref or main_branch or git_utils.get_main_branch()
        production_pipeline = None
        pipelines = api.get_json(
            f"/projects/{project_id}/pipelines",
            per_page=20,
            order_by="updated_at",
            sort="desc",
            ref=ref,
        )
        project_mapping = config.production_mappings.get(str(project_id))
        for pipeline in pipelines or []:
            jobs = api.get_json(f"/projects/{project_id}/pipelines/{pipeline['id']}/jobs")
            if not jobs:
                continue
            for job in jobs:
                if job.get("status", "").lower() != "success":
                    continue
                if _matches_production_job(config, project_mapping, job):
                    production_pipeline = {"pipeline": pipeline, "production_job": job}
                    break
            if production_pipeline:
                break

        if not production_pipeline:
            print("No production deployment found matching pattern")
            return

        _print_deploy(production_pipeline["pipeline"], production_pipeline["production_job"])
    except Exception as error:
        print(f"Error fetching last production deploy: {error}")


def _matches_production_job(config: AppConfig, project_mapping: dict[str, str] | None, job: dict) -> bool:
    job_name = job.get("name", "").lower()
    stage = job.get("stage", "").lower()
    if project_mapping:
        expected_stage = project_mapping.get("stage", "").lower()
        expected_job = project_mapping.get("job", "").lower()
        return stage == expected_stage or (expected_job and job_name == expected_job)
    if config.production_job_name and job_name == config.production_job_name.lower():
        return True
    return stage == config.production_pipeline_name.lower()


def _print_deploy(pipeline: dict, job: dict) -> None:
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
        except ValueError:
            pass
