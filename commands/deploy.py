import datetime

from config import PRODUCTION_MAPPINGS
from git_utils import getMainBranch
from gitlab_api import get_pipeline_jobs, get_recent_pipelines

from .create_issue import get_project_id


def find_production_deployment(pipelines, jobs_loader, project_id, production_mappings):
    for pipeline in pipelines:
        jobs = jobs_loader(project_id, pipeline["id"])
        if jobs is None:
            continue

        for job in jobs:
            job_name = job.get("name", "")
            stage = job.get("stage", "")
            job_status = job.get("status", "").lower()
            if job_status != "success":
                continue

            project_mapping = production_mappings.get(str(project_id))
            if project_mapping:
                expected_stage = project_mapping.get("stage", "").lower()
                expected_job = project_mapping.get("job", "").lower()

                if stage.lower() == expected_stage or (
                    expected_job and job_name.lower() == expected_job
                ):
                    return {
                        "pipeline": pipeline,
                        "production_job": job,
                    }
            else:
                print("Didn't find deployment pipeline")
    return None


def get_last_production_deploy():
    try:
        project_id = get_project_id()
        try:
            ref = getMainBranch()
        except Exception:
            ref = "main"

        pipelines = get_recent_pipelines(project_id, ref=ref)
        if pipelines is None:
            return

        production_pipeline = find_production_deployment(
            pipelines,
            get_pipeline_jobs,
            project_id,
            PRODUCTION_MAPPINGS,
        )

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
        if job.get("duration"):
            print(f"   Duration: {job.get('duration', 'N/A')} seconds")
        else:
            print("   Duration: N/A")
        print(f"   Commit: {pipeline['sha'][:8]}")
        print(f"   URL: {pipeline['web_url']}")

        if job.get("finished_at"):
            try:
                finished_time = datetime.datetime.fromisoformat(
                    job["finished_at"].replace("Z", "+00:00")
                )
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
