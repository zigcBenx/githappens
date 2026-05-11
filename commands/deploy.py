import datetime

import git_utils
from commands.create_issue import resolve_project_id


def _matches_production_mapping(job, mapping):
    expected_stage = mapping.get("stage", "").lower()
    expected_job = mapping.get("job", "").lower()
    stage = job.get("stage", "").lower()
    job_name = job.get("name", "").lower()
    return stage == expected_stage or (expected_job and job_name == expected_job)


def _matches_default_production_job(job, settings):
    stage = job.get("stage", "").lower()
    job_name = job.get("name", "").lower()
    configured_pipeline = (settings.production_pipeline_name or "").lower()
    configured_job = (settings.production_job_name or "").lower()
    return stage == configured_pipeline or (configured_job and job_name == configured_job)


def get_last_production_deploy(api, settings):
    try:
        project_id = resolve_project_id(api)
        try:
            ref = settings.production_ref or git_utils.get_main_branch()
        except Exception:
            ref = "main"

        response = api.list_pipelines(project_id, ref)
        if response.status_code != 200:
            print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
            return

        production_pipeline = None
        for pipeline in response.json():
            jobs_response = api.list_pipeline_jobs(project_id, pipeline["id"])
            if jobs_response.status_code != 200:
                continue

            for job in jobs_response.json():
                if job.get("status", "").lower() != "success":
                    continue

                project_mapping = settings.production_mappings.get(str(project_id))
                if project_mapping:
                    is_match = _matches_production_mapping(job, project_mapping)
                else:
                    is_match = _matches_default_production_job(job, settings)

                if is_match:
                    production_pipeline = {"pipeline": pipeline, "production_job": job}
                    break

            if production_pipeline:
                break

        if not production_pipeline:
            print("No production deployment found matching pattern")
            return

        pipeline = production_pipeline["pipeline"]
        job = production_pipeline["production_job"]

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
                    hours = time_diff.seconds // 3600
                    print(f"   {hours} hours ago")
                else:
                    minutes = time_diff.seconds // 60
                    print(f"   {minutes} minutes ago")
            except Exception:
                pass

    except Exception as error:
        print(f"Error fetching last production deploy: {str(error)}")
