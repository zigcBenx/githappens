import datetime

import config
import git_utils
import gitlab_api
import interactive


def get_last_production_deploy():
    try:
        project_id = interactive.get_project_id()
        if config.MAIN_BRANCH:
            pipeline_ref = config.MAIN_BRANCH
        else:
            try:
                pipeline_ref = git_utils.getMainBranch()
            except Exception:
                pipeline_ref = "main"

        result = gitlab_api.get_last_production_deploy_info(project_id, ref=pipeline_ref)
        if result.get('error') == 'pipelines_fetch':
            print(f"Failed to fetch pipelines: {result['status']} - {result['text']}")
            return
        if result.get('error') == 'not_found':
            print(f"No production deployment found matching pattern")
            return

        pipeline = result['pipeline']
        job = result['production_job']

        print(f"🚀 Last Production Deployment:")
        print(f"   Pipeline: #{pipeline['id']} - {pipeline['status']}")
        print(f"   Job: {job['name']} ({job['status']})")
        print(f"   Branch/Tag: {pipeline['ref']}")
        print(f"   Started: {job.get('started_at', 'N/A')}")
        print(f"   Finished: {job.get('finished_at', 'N/A')}")
        print(f"   Duration: {job.get('duration', 'N/A')} seconds" if job.get('duration') else "   Duration: N/A")
        print(f"   Commit: {pipeline['sha'][:8]}")
        print(f"   URL: {pipeline['web_url']}")

        if job.get('finished_at'):
            try:
                finished_time = datetime.datetime.fromisoformat(job['finished_at'].replace('Z', '+00:00'))
                time_diff = datetime.datetime.now(datetime.timezone.utc) - finished_time

                if time_diff.days > 0:
                    print(f"   ⏰ {time_diff.days} days ago")
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    print(f"   ⏰ {hours} hours ago")
                else:
                    minutes = time_diff.seconds // 60
                    print(f"   ⏰ {minutes} minutes ago")
            except Exception:
                pass

    except Exception as e:
        print(f"Error fetching last production deploy: {str(e)}")
