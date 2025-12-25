import subprocess
import json
import datetime
import requests
import re
import webbrowser

from config import get_config
from git_utils import get_project_link_from_current_dir, get_current_branch, get_main_branch


def get_all_projects(project_link):
    config = get_config()
    url = config.API_URL + "/projects?membership=true&search=" + project_link.split('/')[-1].split('.')[0]
    
    headers = {
        "PRIVATE-TOKEN": config.GITLAB_TOKEN
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        exit(1)
    else:
        print(f"Request failed with status code {response.status_code}")
        return None


def get_project_id():
    project_link = get_project_link_from_current_dir()
    if project_link == -1:
        # imported here to avoid circular dependency
        from interactive import enter_project_id
        return enter_project_id()
    
    all_projects = get_all_projects(project_link)
    # Find projects id by project ssh link gathered from repo
    matching_id = None
    for project in all_projects:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def list_milestones(current=False):
    config = get_config()
    cmd = f'glab api /groups/{config.GROUP_ID}/milestones?state=active'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    milestones = json.loads(result.stdout)
    if current:
        today = datetime.date.today().strftime('%Y-%m-%d')
        active_milestones = []
        for milestone in milestones:
            start_date = milestone['start_date']
            due_date = milestone['due_date']
            if start_date and due_date and start_date <= today and due_date >= today:
                active_milestones.append(milestone)
            if not active_milestones:
                return None
        active_milestones.sort(key=lambda x: x['due_date'])
        return active_milestones[0]
    return milestones


def list_iterations():
    config = get_config()
    cmd = f'glab api /groups/{config.GROUP_ID}/iterations?state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    iterations = json.loads(result.stdout)
    return iterations


def list_epics():
    config = get_config()
    cmd = f'glab api /groups/{config.GROUP_ID}/epics?per_page=1000&state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def execute_issue_create(project_id, title, labels, milestone_id, epic, iteration, weight, estimated_time, issue_type='issue'):
    config = get_config()
    labels = ",".join(labels) if type(labels) == list else labels
    assignee_id = get_authorized_user()['id']
    issue_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f'title={title}',
        "-f", f'assignee_ids={assignee_id}',
        "-f", f'issue_type={issue_type}'
    ]
    if labels:
        issue_command.append("-f")
        issue_command.append(f'labels={labels}')
    
    if weight:
        issue_command.append("-f")
        issue_command.append(f'weight={str(weight)}')
    
    if milestone_id:
        issue_command.append("-f")
        issue_command.append(f'milestone_id={str(milestone_id)}')
    
    if epic:
        epic_id = epic['id']
        issue_command.append("-f")
        issue_command.append(f'epic_id={str(epic_id)}')
    
    # Set the description, including iteration, estimated time, and other info
    description = ""
    if iteration:
        iteration_id = iteration['id']
        description += f"/iteration *iteration:{str(iteration_id)} "
    
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    
    issue_command.extend(["-f", f'description={description}'])
    
    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_branch(project_id, issue, main_branch):
    issue_id = str(issue['iid'])
    title = re.sub('\\s+', '-', issue['title']).lower()
    title = issue_id + '-' + title.replace(':', '').replace('(', ' ').replace(')', '').replace(' ', '-')
    branch_output = subprocess.check_output(["glab", "api", f"/projects/{str(project_id)}/repository/branches", "-f", f'branch={title}', "-f", f'ref={main_branch}', "-f", f'issue_iid={issue_id}'])
    return json.loads(branch_output.decode())


def create_merge_request(project_id, branch, issue, labels, milestone_id, main_branch):
    config = get_config()
    issue_id = str(issue['iid'])
    branch_name = branch['name']
    title = issue['title']
    assignee_id = get_authorized_user()['id']
    labels = ",".join(labels) if type(labels) == list else labels
    merge_request_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f", f'title={title}',
        "-f", f'description="Closes #{issue_id}"',
        "-f", f'source_branch={branch_name}',
        "-f", f'target_branch={main_branch}',
        "-f", f'issue_iid={issue_id}',
        "-f", f'assignee_ids={assignee_id}'
    ]
    
    if config.SQUASH_COMMITS:
        merge_request_command.append("-f")
        merge_request_command.append("squash=true")
    
    if config.DELETE_BRANCH:
        merge_request_command.append("-f")
        merge_request_command.append("remove_source_branch=true")
    
    if labels:
        merge_request_command.append("-f")
        merge_request_command.append(f'labels={labels}')
    
    if milestone_id:
        merge_request_command.append("-f")
        merge_request_command.append(f'milestone_id={str(milestone_id)}')
    
    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())


def get_merge_request_for_branch(branch_name):
    """Get merge request for a given branch."""
    config = get_config()
    project_id = get_project_id()
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests"
    headers = {"Private-Token": config.GITLAB_TOKEN}
    
    params = {
        "source_branch": branch_name,
    }
    
    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        merge_requests = response.json()
        for mr in merge_requests:
            if mr["source_branch"] == branch_name:
                return mr
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def add_reviewers_to_merge_request(reviewers=None):
    """Add reviewers to a merge request."""
    config = get_config()
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": config.GITLAB_TOKEN}
    
    data = {
        "reviewer_ids": reviewers if reviewers is not None else config.REVIEWERS
    }
    
    requests.put(api_url, headers=headers, json=data)


def set_merge_request_to_auto_merge():
    """Set merge request to auto-merge when pipeline succeeds."""
    config = get_config()
    project_id = get_project_id()
    mr_id = get_active_merge_request_id()
    api_url = f"{config.API_URL}/projects/{project_id}/merge_requests/{mr_id}/merge"
    headers = {"Private-Token": config.GITLAB_TOKEN}
    
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    
    requests.put(api_url, headers=headers, json=data)


def get_labels_of_group(search=''):
    """Get labels from a group."""
    config = get_config()
    cmd = f'glab api /groups/{config.GROUP_ID}/labels?search={search}'
    try:
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting labels: {str(e)}")
        return []


def close_opened_issue(issue_iid, project_id):
    """Close an issue."""
    issue_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        '-X', 'PUT',
        '-f', 'state_event=close'
    ]
    try:
        subprocess.run(issue_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"Error closing issue: {str(e)}")


def get_active_merge_request_id():
    """Get the active merge request ID for current branch."""
    branch_to_find = get_current_branch()
    return find_merge_request_id_by_branch(branch_to_find)


def find_merge_request_id_by_branch(branch_name):
    """Find merge request ID by branch name."""
    return get_merge_request_for_branch(branch_name)['iid']


def get_last_production_deploy():
    """Get information about the last production deployment."""
    config = get_config()
    try:
        project_id = get_project_id()
        api_url = f"{config.API_URL}/projects/{project_id}/pipelines"
        headers = {"Private-Token": config.GITLAB_TOKEN}
        
        # Set up parameters for the pipeline search
        params = {
            "per_page": 50,
            "order_by": "updated_at",
            "sort": "desc"
        }
        
        # Add ref filter if specified in config
        main_branch = get_main_branch()
        if main_branch:
            params["ref"] = main_branch
        else:
            # Fallback to common main branch names
            params["ref"] = "main"
        
        response = requests.get(api_url, headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
            return
        
        pipelines = response.json()
        production_pipeline = None
        
        # Look for production pipeline by name pattern
        for pipeline in pipelines:
            # Get pipeline details to check jobs
            pipeline_detail_url = f"{config.API_URL}/projects/{project_id}/pipelines/{pipeline['id']}/jobs"
            detail_response = requests.get(pipeline_detail_url, headers=headers)
            
            if detail_response.status_code == 200:
                jobs = detail_response.json()
                
                # Check if this pipeline contains production deployment
                for job in jobs:
                    job_name = job.get('name', '')
                    stage = job.get('stage', '')
                    job_status = job.get('status', '').lower()
                    
                    # Only consider successful jobs
                    if job_status != 'success':
                        continue
                    
                    # Check project-specific mapping first
                    project_mapping = config.PRODUCTION_MAPPINGS.get(str(project_id))
                    if project_mapping:
                        expected_stage = project_mapping.get('stage', '').lower()
                        expected_job = project_mapping.get('job', '').lower()
                        
                        if (stage.lower() == expected_stage or
                            (expected_job and job_name.lower() == expected_job)):
                            production_pipeline = {
                                'pipeline': pipeline,
                                'production_job': job
                            }
                            break
                    else:
                        print('Didn\'t find deployment pipeline')
                
                if production_pipeline:
                    break
        
        if not production_pipeline:
            print(f"No production deployment found matching pattern")
            return
        
        # Display the results
        pipeline = production_pipeline['pipeline']
        job = production_pipeline['production_job']
        
        print(f"🚀 Last Production Deployment:")
        print(f"   Pipeline: #{pipeline['id']} - {pipeline['status']}")
        print(f"   Job: {job['name']} ({job['status']})")
        print(f"   Branch/Tag: {pipeline['ref']}")
        print(f"   Started: {job.get('started_at', 'N/A')}")
        print(f"   Finished: {job.get('finished_at', 'N/A')}")
        print(f"   Duration: {job.get('duration', 'N/A')} seconds" if job.get('duration') else "   Duration: N/A")
        print(f"   Commit: {pipeline['sha'][:8]}")
        print(f"   URL: {pipeline['web_url']}")
        
        # Show time since deployment
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
            except:
                pass
        
    except Exception as e:
        print(f"Error fetching last production deploy: {str(e)}")


def open_merge_request_in_browser():
    config = get_config()
    try:
        merge_request_id = get_active_merge_request_id()
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        url = config.BASE_URL + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None


def get_current_issue_id():
    mr = get_merge_request_for_branch(get_current_branch())
    return mr['description'].replace('"', '').replace('#', '').split()[1]

