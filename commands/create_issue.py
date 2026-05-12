"""Issue, branch and MR creation logic."""
import re

import config
import gitlab_api
import interactive


def execute_issue_create(project_id, title, labels, milestone_id, epic, iteration,
                        weight, estimated_time, issue_type='issue'):
    labels = ",".join(labels) if isinstance(labels, list) else labels
    assignee_id = gitlab_api.get_authorized_user()['id']

    fields = [
        ('title', title),
        ('assignee_ids', assignee_id),
        ('issue_type', issue_type),
    ]
    if labels:
        fields.append(('labels', labels))
    if weight:
        fields.append(('weight', str(weight)))
    if milestone_id:
        fields.append(('milestone_id', str(milestone_id)))
    if epic:
        fields.append(('epic_id', str(epic['id'])))

    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    fields.append(('description', description))

    return gitlab_api.create_issue_via_glab(project_id, fields)


def create_issue(title, project_id, milestone_id, epic, iteration, settings):
    if not settings:
        print("No settings in template")
        exit(2)
    issue_type = settings.get('type') or 'issue'
    return execute_issue_create(
        project_id, title, settings.get('labels'), milestone_id, epic, iteration,
        settings.get('weight'), settings.get('estimated_time'), issue_type,
    )


def create_branch(project_id, issue):
    issue_id = str(issue['iid'])
    title = re.sub('\\s+', '-', issue['title']).lower()
    title = issue_id + '-' + title.replace(':', '').replace('(', ' ').replace(')', '').replace(' ', '-')
    return gitlab_api.create_branch_via_glab(project_id, title, config.MAIN_BRANCH, issue_id)


def create_merge_request(project_id, branch, issue, labels, milestone_id):
    issue_id = str(issue['iid'])
    branch_name = branch['name']
    title = issue['title']
    assignee_id = gitlab_api.get_authorized_user()['id']
    labels = ",".join(labels) if isinstance(labels, list) else labels

    fields = [
        ('title', title),
        ('description', f'"Closes #{issue_id}"'),
        ('source_branch', branch_name),
        ('target_branch', config.MAIN_BRANCH),
        ('issue_iid', issue_id),
        ('assignee_ids', assignee_id),
    ]
    if config.SQUASH_COMMITS:
        fields.append(('squash', 'true'))
    if config.DELETE_BRANCH:
        fields.append(('remove_source_branch', 'true'))
    if labels:
        fields.append(('labels', labels))
    if milestone_id:
        fields.append(('milestone_id', str(milestone_id)))

    return gitlab_api.create_merge_request_via_glab(project_id, fields)


def start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue):
    estimated_time = interactive.prompt_estimated_time()

    if isinstance(project_id, list):
        estimated_time_per_project = (
            int(estimated_time) / len(project_id) if estimated_time else None
        )
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings['estimated_time'] = int(estimated_time_per_project)

    created_issue = create_issue(title, project_id, milestone, epic, iteration, selected_settings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = create_branch(project_id, created_issue)
    created_mr = create_merge_request(
        project_id, created_branch, created_issue,
        selected_settings.get('labels'), milestone,
    )
    print(f"Merge request #{created_mr['iid']}: {created_mr['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_mr['source_branch']}' 'origin/{created_mr['source_branch']}'")
    print("to switch to new branch.")

    return created_issue
