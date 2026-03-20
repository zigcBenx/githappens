import inquirer

import gitlab_api


def createIssue(title, project_id, milestoneId, epic, iteration, settings):
    if settings:
        issueType = settings.get('type') or 'issue'
        return gitlab_api.executeIssueCreate(project_id, title, settings.get('labels'), milestoneId, epic, iteration, settings.get('weight'), settings.get('estimated_time'), issueType)
    print("No settings in template")
    exit(2)
    pass


def startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue):
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
        selectedSettings = selectedSettings.copy() if selectedSettings else {}
        selectedSettings['estimated_time'] = int(estimated_time_per_project)

    createdIssue = createIssue(title, project_id, milestone, epic, iteration, selectedSettings)
    print(f"Issue #{createdIssue['iid']}: {createdIssue['title']} created.")

    if onlyIssue:
        return createdIssue

    createdBranch = gitlab_api.create_branch(project_id, createdIssue)

    createdMergeRequest = gitlab_api.create_merge_request(project_id, createdBranch, createdIssue, selectedSettings.get('labels'), milestone)
    print(f"Merge request #{createdMergeRequest['iid']}: {createdMergeRequest['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{createdMergeRequest['source_branch']}' 'origin/{createdMergeRequest['source_branch']}'")
    print("to switch to new branch.")

    return createdIssue
