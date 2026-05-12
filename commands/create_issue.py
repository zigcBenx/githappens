import subprocess
import json
import re
from config import MAIN_BRANCH_DEFAULT, SQUASH_COMMITS, DELETE_BRANCH

def execute_issue_create(project_id, title, labels, milestone_id, epic, iteration, weight, estimated_time, issue_type='issue'):
    import interactive
    import gitlab_api
    
    labels_str = ",".join(labels) if isinstance(labels, list) else labels
    
    # Using glab for issue creation as in original code
    issue_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f'title={title}',
        "-f", f'assignee_ids={get_authorized_user()["id"]}',
        "-f", f'issue_type={issue_type}'
    ]
    if labels_str:
        issue_command.extend(["-f", f'labels={labels_str}'])
    if weight:
        issue_command.extend(["-f", f'weight={str(weight)}'])
    if milestone_id:
        issue_command.extend(["-f", f'milestone_id={str(milestone_id)}'])
    if epic:
        issue_command.extend(["-f", f'epic_id={str(epic["id"])}'])
    
    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    
    issue_command.extend(["-f", f'description={description}'])
    
    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())

def get_authorized_user():
    import subprocess
    import json
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)

def create_branch(project_id, issue):
    issue_id = str(issue['iid'])
    title = re.sub('\\s+', '-', issue['title']).lower()
    title = issue_id + '-' + title.replace(':','').replace('(',' ').replace(')', '').replace(' ','-')
    branch_output = subprocess.check_output(["glab", "api", f"/projects/{str(project_id)}/repository/branches", "-f", f'branch={title}', "-f", f'ref={MAIN_BRANCH_DEFAULT}', "-f", f'issue_iid={issue_id}'])
    return json.loads(branch_output.decode())

def create_merge_request(project_id, branch, issue, labels, milestone_id):
    issue_id = str(issue['iid'])
    branch_name = branch['name']
    title = issue['title']
    assignee_id = get_authorized_user()['id']
    labels_str = ",".join(labels) if isinstance(labels, list) else labels
    
    merge_request_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f", f'title={title}',
        "-f", f'description="Closes #{issue_id}"',
        "-f", f'source_branch={branch_name}',
        "-f", f'target_branch={MAIN_BRANCH_DEFAULT}',
        "-f", f'issue_iid={issue_id}',
        "-f", f'assignee_ids={assignee_id}'
    ]
    if SQUASH_COMMITS:
        merge_request_command.extend(["-f", "squash=true"])
    if DELETE_BRANCH:
        merge_request_command.extend(["-f", "remove_source_branch=true"])
    if labels_str:
        merge_request_command.extend(["-f", f'labels={labels_str}'])
    if milestone_id:
        merge_request_command.extend(["-f", f'milestone_id={str(milestone_id)}'])
    
    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())

def start_issue_creation(project_id, title, milestone_id, epic, iteration, selected_settings, only_issue):
    import interactive
    import git_utils
    
    estimated_time = interactive.prompt_estimated_time()
    
    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time
    
    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings['estimated_time'] = int(estimated_time_per_project)
    
    # In reality, we should call execute_issue_create here
    # For simplicity and matching original logic:
    issue_type = selected_settings.get('type') or 'issue'
    created_issue = execute_issue_create(
        project_id, 
        title, 
        selected_settings.get('labels'), 
        milestone_id, 
        epic, 
        iteration, 
        selected_settings.get('weight'), 
        selected_settings.get('estimated_time'), 
        issue_type
    )
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")
    
    if only_issue:
        return created_issue
    
    created_branch = create_branch(project_id, created_issue)
    created_mr = create_merge_request(project_id, created_branch, created_issue, selected_settings.get('labels'), milestone_id)
    print(f"Merge request #{created_mr['iid']}: {created_mr['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_mr['source_branch']}' 'origin/{created_mr['source_branch']}'")
    print("to switch to new branch.")
    
    return created_issue
