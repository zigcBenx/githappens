import datetime

import requests

from .. import config, git_utils, templates
from .create_issue import get_project_id


def get_last_production_deploy():
    try:
        project_id = get_project_id()
        api_url = f"{config.API_URL}/projects/{project_id}/pipelines"
        headers = {"Private-Token": config.GITLAB_TOKEN}
        params = {"per_page": 50, "order_by": "updated_at", "sort": "desc"}

        if config.MAIN_BRANCH:
            params["ref"] = config.MAIN_BRANCH
        else:
            try:
                params["ref"] = git_utils.get_main_branch()
            except Exception:
                params["ref"] = "main"

        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
            return

        production_pipeline = None
        for pipeline in response.json():
            detail_response = requests.get(
                f"{config.API_URL}/projects/{project_id}/pipelines/{pipeline['id']}/jobs",
                headers=headers,
            )
            if detail_response.status_code == 200:
                for job in detail_response.json():
                    job_name = job.get("name", "")
                    stage = job.get("stage", "")
                    job_status = job.get("status", "").lower()

                    if job_status != "success":
                        continue

                    project_mapping = templates.get_production_mappings().get(str(project_id))
                    if project_mapping:
                        expected_stage = project_mapping.get("stage", "").lower()
                        expected_job = project_mapping.get("job", "").lower()
                        if stage.lower() == expected_stage or (
                            expected_job and job_name.lower() == expected_job
                        ):
                            production_pipeline = {"pipeline": pipeline, "production_job": job}
                            break
                    else:
                        print("Didn't find deployment pipeline")

                if production_pipeline:
                    break

        if not production_pipeline:
            print("No production deployment found matching pattern")
            return

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

        if job.get("finished_at"):
            try:
                finished_time = datetime.datetime.fromisoformat(
                    job["finished_at"].replace("Z", "+00:00")
                )
                time_diff = datetime.datetime.now(datetime.timezone.utc) - finished_time
                if time_diff.days > 0:
                    print(f"   ⏰ {time_diff.days} days ago")
                elif time_diff.seconds > 3600:
                    print(f"   ⏰ {time_diff.seconds // 3600} hours ago")
                else:
                    print(f"   ⏰ {time_diff.seconds // 60} minutes ago")
            except Exception:
                pass
    except Exception as error:
        print(f"Error fetching last production deploy: {str(error)}")
