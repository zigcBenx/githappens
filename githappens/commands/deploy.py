from __future__ import annotations

import datetime


def get_last_production_deploy(runtime, client, project_id):
    ref = runtime.config.production_ref or "master"

    pipelines = client.get_pipelines(
        project_id,
        per_page=50,
        order_by="updated_at",
        sort="desc",
        ref=ref,
    )

    production_pipeline = None
    for pipeline in pipelines:
        jobs = client.get_pipeline_jobs(project_id, pipeline["id"])
        for job in jobs:
            if job.get("status", "").lower() != "success":
                continue

            mapping = runtime.production_mappings.get(str(project_id))
            if not mapping:
                continue

            expected_stage = mapping.get("stage", "").lower()
            expected_job = mapping.get("job", "").lower()
            stage = job.get("stage", "").lower()
            job_name = job.get("name", "").lower()

            if stage == expected_stage or (expected_job and job_name == expected_job):
                production_pipeline = {"pipeline": pipeline, "production_job": job}
                break
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
    print(
        f"   Duration: {job.get('duration', 'N/A')} seconds"
        if job.get("duration")
        else "   Duration: N/A"
    )
    print(f"   Commit: {pipeline['sha'][:8]}")
    print(f"   URL: {pipeline['web_url']}")

    finished_at = job.get("finished_at")
    if not finished_at:
        return

    finished_time = datetime.datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
    time_diff = datetime.datetime.now(datetime.timezone.utc) - finished_time
    if time_diff.days > 0:
        print(f"   ⏰ {time_diff.days} days ago")
    elif time_diff.seconds > 3600:
        print(f"   ⏰ {time_diff.seconds // 3600} hours ago")
    else:
        print(f"   ⏰ {time_diff.seconds // 60} minutes ago")
