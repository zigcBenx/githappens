import subprocess
import datetime
from config import API_URL, GITLAB_TOKEN, MAIN_BRANCH_DEFAULT, PRODUCTION_MAPPINGS
import gitlab_api
import git_utils
from commands.common import get_project_id

def check_last_production_deploy():
    try:
        project_id = get_project_id()
        ref = MAIN_BRANCH_DEFAULT
        try:
            ref = git_utils.get_main_branch()
        except:
            pass
            
        pipelines = gitlab_api.get_pipelines(project_id, ref=ref)
        if not pipelines:
            print("No pipelines found.")
            return

        for pipeline in pipelines:
            jobs = gitlab_api.get_pipeline_jobs(project_id, pipeline['id'])
            if not jobs: continue
            
            for job in jobs:
                job_name = job.get('name', '')
                stage = job.get('stage', '')
                job_status = job.get('status', '').lower()
                
                if job_status != 'success': continue
                
                project_mapping = PRODUCTION_MAPPINGS.get(str(project_id))
                if project_mapping:
                    expected_stage = project_mapping.get('stage', '').lower()
                    expected_job = project_mapping.get('job', '').lower()
                    if stage.lower() == expected_stage or (expected_job and job_name.lower() == expected_job):
                        display_deploy_info(pipeline, job)
                        return
                else:
                    # If no mapping, original code printed 'Didn't find deployment pipeline' inside loop
                    # We'll just continue searching
                    pass
        
        print(f"No production deployment found matching pattern")
    except Exception as e:
        print(f"Error fetching last production deploy: {str(e)}")

def display_deploy_info(pipeline, job):
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
                print(f"   ⏰ {time_diff.seconds // 3600} hours ago")
            else:
                print(f"   ⏰ {time_diff.seconds // 60} minutes ago")
        except:
            pass
