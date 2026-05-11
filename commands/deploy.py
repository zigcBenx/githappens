import datetime

import requests

import config
import git_utils
import gitlab_api as api
import templates


def get_last_production_deploy():
    try:
        project_id = api.get_project_id()
        api_url = f"{config.API_URL}/projects/{project_id}/pipelines"
        params = {
            "per_page": 50,
            "order_by": "updated_at",
            "sort": "desc",
        }

        if config.MAIN_BRANCH:
            params["ref"] = config.MAIN_BRANCH
        else:
            try:
                params["ref"] = git_utils.get_main_branch()
            except Exception:
                params["ref"] = "main"

        response = requests.get(api_url, headers=api.token_headers(), params=params)
        if response.status_code != 200:
            print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
            return

        production_pipeline = None
        for pipeline in response.json():
            jobs_url = f"{config.API_URL}/projects/{project_id}/pipelines/{pipeline['id']}/jobs"
            jobs_response = requests.get(jobs_url, headers=api.token_headers())
            if jobs_response.status_code != 200:
                continue

            for job in jobs_response.json():
                if job.get("status", "").lower() != "success":
                    continue

                project_mapping = templates.PRODUCTION_MAPPINGS.get(str(project_id))
                if not project_mapping:
                    print("Didn't find deployment pipeline")
                    continue

                expected_stage = project_mapping.get("stage", "").lower()
                expected_job = project_mapping.get("job", "").lower()
                stage_matches = job.get("stage", "").lower() == expected_stage
                job_matches = expected_job and job.get("name", "").lower() == expected_job
                if stage_matches or job_matches:
                    production_pipeline = {"pipeline": pipeline, "production_job": job}
                    break

            if production_pipeline:
                break

        if not production_pipeline:
            print("No production deployment found matching pattern")
            return

        _print_production_deploy(production_pipeline["pipeline"], production_pipeline["production_job"])
    except Exception as error:
        print(f"Error fetching last production deploy: {str(error)}")


def _print_production_deploy(pipeline, job):
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
