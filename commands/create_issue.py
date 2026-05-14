from config import API_URL, GITLAB_TOKEN, MAIN_BRANCH
from templates import TEMPLATES
from gitlab_api import create_branch, create_merge_request
from interactive import select_template, getIssueSettings, get_milestone, get_iteration, get_epic


def createIssue(title, project_id, milestoneId, epic, iteration, settings):
    if settings:
        issueType = settings.get('type') or 'issue'
        return executeIssueCreate(project_id, title, settings.get('labels'), milestoneId, epic, iteration, settings.get('weight'), settings.get('estimated_time'), issueType)
    print("No settings in template")
    exit(2)
    pass

def executeIssueCreate(project_id, title, labels, milestoneId, epic, iteration, weight, estimated_time, issue_type='issue'):
    labels = ",".join(labels) if type(labels) == list else labels
    assignee_id = getAuthorizedUser()['id']
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

    if milestoneId:
        issue_command.append("-f")
        issue_command.append(f'milestone_id={str(milestoneId)}')

    if epic:
        epicId = epic['id']
        issue_command.append("-f")
        issue_command.append(f'epic_id={str(epicId)}')

    # Set the description, including iteration, estimated time, and other info
    description = ""
    if iteration:
        iterationId = iteration['id']
        description += f"/iteration *iteration:{str(iterationId)} "

    if estimated_time:
        description += f"\n/estimate {estimated_time}m "

    issue_command.extend(["-f", f'description={description}'])

    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())

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

    createdBranch = create_branch(project_id, createdIssue)

    createdMergeRequest = create_merge_request(project_id, createdBranch, createdIssue, selectedSettings.get('labels'), milestone)
    print(f"Merge request #{createdMergeRequest['iid']}: {createdMergeRequest['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{createdMergeRequest['source_branch']}' 'origin/{createdMergeRequest['source_branch']}'")
    print("to switch to new branch.")

    return createdIssue

