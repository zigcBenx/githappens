"""Interactive CLI prompts using inquirer."""
import inquirer
from gitlab_api import createIssue, create_branch, create_merge_request


def startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue):
    estimated_time = inquirer.prompt([
        inquirer.Text('estimated_time',
                      message='Estimated time to complete this issue (in minutes, optional)',
                      validate=lambda _, x: x == '' or x.isdigit())
    ])['estimated_time']
    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time
    if estimated_time_per_project:
        selectedSettings = (selectedSettings or {}).copy()
        selectedSettings['estimated_time'] = int(estimated_time_per_project)
    createdIssue = createIssue(title, project_id, milestone, epic, iteration, selectedSettings)
    print(f"Issue #{createdIssue['iid']}: {createdIssue['title']} created.")
    if onlyIssue:
        return createdIssue
    createdBranch = create_branch(project_id, createdIssue)
    createdMergeRequest = create_merge_request(
        project_id, createdBranch, createdIssue,
        selectedSettings.get('labels'), milestone
    )
    print(f"Merge request #{createdMergeRequest['iid']}: {createdMergeRequest['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{createdMergeRequest['source_branch']}' 'origin/{createdMergeRequest['source_branch']}'")
    return createdIssue