import inquirer

from gitlab_api import execute_issue_create, create_branch, create_merge_request
from git_utils import get_main_branch


def create_issue(title, project_id, milestone_id, epic, iteration, settings):
    if settings:
        issue_type = settings.get('type') or 'issue'
        return execute_issue_create(project_id, title, settings.get('labels'), milestone_id, epic, iteration, settings.get('weight'), settings.get('estimated_time'), issue_type)
    print("No settings in template")
    exit(2)


def start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue):
    # Prompt for estimated time
    estimated_time = inquirer.prompt([
        inquirer.Text('estimated_time',
                      message='Estimated time to complete this issue (in minutes, optional)',
                      validate=lambda _, x: x == '' or x.isdigit())
    ])['estimated_time']
    
    # If multiple project IDs, split the estimated time
    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time
    
    # Modify settings to include estimated time
    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings['estimated_time'] = int(estimated_time_per_project)
    
    created_issue = create_issue(title, project_id, milestone, epic, iteration, selected_settings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")
    
    if only_issue:
        return created_issue
    
    main_branch = get_main_branch()
    created_branch = create_branch(project_id, created_issue, main_branch)
    
    created_merge_request = create_merge_request(project_id, created_branch, created_issue, selected_settings.get('labels'), milestone, main_branch)
    print(f"Merge request #{created_merge_request['iid']}: {created_merge_request['title']} created.")
    
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_merge_request['source_branch']}' 'origin/{created_merge_request['source_branch']}'")
    print("to switch to new branch.")
    
    return created_issue
