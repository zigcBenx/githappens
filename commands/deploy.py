#!/usr/bin/env python3
import datetime

import config
import gitlab_api
import git_utils


def run():
    try:
        project_id = gitlab_api.get_project_id()
        params = {
            "per_page": 50,
            "order_by": "updated_at",
            "sort": "desc",
        }
        if config.MAIN_BRANCH:
            params["ref"] = config.MAIN_BRANCH
        else:
            try:
                main_branch = git_utils.get_main_branch()
                params["ref"] = main_branch
            except Exception:
                params["ref"] = "main"

        pipelines = gitlab_api.get_pipelines(project_id, params)
        if not pipelines:
            print("Failed to fetch pipelines.")
            return

        production_pipeline = None
        for pipeline in pipelines:
            jobs = gitlab_api.get_pipeline_jobs(project_id, pipeline['id'])
            if not jobs:
                continue

            for job in jobs:
                job_name = job.get('name', '')
                stage = job.get('stage', '')
                job_status = job.get('status', '').lower()

                if job_status != 'success':
                    continue

                project_mapping = config.PRODUCTION_MAPPINGS.get(str(project_id))
                if project_mapping:
                    expected_stage = project_mapping.get('stage', '').lower()
                    expected_job = project_mapping.get('job', '').lower()

                    if (stage.lower() == expected_stage or
                            (expected_job and job_name.lower() == expected_job)):
                        production_pipeline = {
                            'pipeline': pipeline,
                            'production_job': job,
                        }
                        break
                else:
                    print("Didn't find deployment pipeline")

            if production_pipeline:
                break

        if not production_pipeline:
            print("No production deployment found matching pattern")
            return

        pipeline = production_pipeline['pipeline']
        job = production_pipeline['production_job']

        print(f"Last Production Deployment:")
        print(f"   Pipeline: #{pipeline['id']} - {pipeline['status']}")
        print(f"   Job: {job['name']} ({job['status']})")
        print(f"   Branch/Tag: {pipeline['ref']}")
        print(f"   Started: {job.get('started_at', 'N/A')}")
        print(f"   Finished: {job.get('finished_at', 'N/A')}")
        if job.get('duration'):
            print(f"   Duration: {job['duration']} seconds")
        else:
            print("   Duration: N/A")
        print(f"   Commit: {pipeline['sha'][:8]}")
        print(f"   URL: {pipeline['web_url']}")

        if job.get('finished_at'):
            try:
                finished_time = datetime.datetime.fromisoformat(job['finished_at'].replace('Z', '+00:00'))
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

    except Exception as e:
        print(f"Error fetching last production deploy: {str(e)}")
