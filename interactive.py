import subprocess

import inquirer
import requests

import config
import git_utils
import gitlab_api


def get_project_id():
    project_link = git_utils.getProjectLinkFromCurrentDir()
    if (project_link == -1):
        return enterProjectId()

    allProjects = gitlab_api.get_all_projects(project_link)
    # Find projects id by project ssh link gathered from repo
    matching_id = None
    for project in allProjects:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def enterProjectId():
    while True:
        project_id = input('Please enter the ID of your GitLab project: ')
        if project_id:
            return project_id
        exit('Invalid project ID.')


def select_milestone(milestones):
    milestones = [t['title'] for t in milestones]
    questions = [
        inquirer.List('milestones',
                      message="Select milestone:",
                      choices=milestones,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['milestones']


def getSelectedMilestone(milestone, milestones):
    return next((t for t in milestones if t['title'] == milestone), None)


def get_milestone(manual):
    if manual:
        milestones = gitlab_api.list_milestones()
        return getSelectedMilestone(select_milestone(milestones), milestones)
    milestone = gitlab_api.list_milestones(True)  # select active for today
    return milestone


def get_iteration(manual):
    if manual:
        iterations = gitlab_api.list_iterations()
        return getSelectedIteration(select_iteration(iterations), iterations)
    return gitlab_api.getActiveIteration()


def getSelectedIteration(iteration, iterations):
    return next((t for t in iterations if t['start_date'] + ' - ' + t['due_date'] == iteration), None)


def select_iteration(iterations):
    iterations = [t['start_date'] + ' - ' + t['due_date'] for t in iterations]
    questions = [
        inquirer.List('iterations',
                      message="Select iteration:",
                      choices=iterations,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['iterations']


def select_epic(epics):
    epics = [t['title'] for t in epics]
    search_query = inquirer.prompt([
        inquirer.Text('search_query', message='Search epic:'),
    ])['search_query']

    # Filter choices based on search query
    filtered_epics = [c for c in epics if search_query.lower() in c.lower()]
    questions = [
        inquirer.List('epics',
                      message="Select epic:",
                      choices=filtered_epics,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['epics']


def getSelectedEpic(epic, epics):
    return next((t for t in epics if t['title'] == epic), None)


def get_epic():
    epics = gitlab_api.list_epics()
    return getSelectedEpic(select_epic(epics), epics)


def chooseReviewersManually():
    """Prompt the user to select reviewers manually from the available list, showing names."""
    # Fetch user details for each reviewer ID
    reviewer_choices = []
    for reviewer_id in config.REVIEWERS:
        api_url = f"{config.API_URL}/users/{reviewer_id}"
        headers = {"Private-Token": config.GITLAB_TOKEN}
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                user = response.json()
                display_name = f"{user.get('name')} ({user.get('username')})"
                reviewer_choices.append((display_name, reviewer_id))
            else:
                reviewer_choices.append((str(reviewer_id), reviewer_id))
        except Exception:
            reviewer_choices.append((str(reviewer_id), reviewer_id))

    questions = [
        inquirer.Checkbox(
            "selected_reviewers",
            message="Select reviewers",
            choices=[(name, str(rid)) for name, rid in reviewer_choices],
        )
    ]
    answers = inquirer.prompt(questions)
    if answers and "selected_reviewers" in answers:
        return [int(r) for r in answers["selected_reviewers"]]
    else:
        return []


def selectLabels(search, multiple=False):
    labels = gitlab_api.getLabelsOfGroup(search)
    labels = sorted([t['name'] for t in labels])

    question_type = inquirer.Checkbox if multiple else inquirer.List
    questions = [
        question_type(
            'labels',
            message="Select one or more department labels:",
            choices=labels,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer['labels']


def getCurrentIssueId():
    mr = gitlab_api.getMergeRequestForBranch(get_project_id(), git_utils.getCurrentBranch())
    return mr['description'].replace('"', '').replace('#', '').split()[1]


def track_issue_time():
    # Get the current merge request
    try:
        project_id = get_project_id()
        issue_id = getCurrentIssueId()
    except Exception as e:
        print(f"Error getting issue details: {str(e)}")
        return

    # Prompt for actual time spent
    spent_time = inquirer.prompt([
        inquirer.Text('spent_time',
                      message='How many minutes did you actually spend on this issue?',
                      validate=lambda _, x: x.isdigit())
    ])['spent_time']

    # Add spent time to the issue description
    time_tracking_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_id}/notes",
        "-f", f"body=/spend {spent_time}m"
    ]

    try:
        subprocess.run(time_tracking_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except subprocess.CalledProcessError as e:
        print(f"Error adding time tracking: {str(e)}")
    except Exception as e:
        print(f"Error tracking issue time: {str(e)}")


def getActiveMergeRequestId():
    branch_to_find = git_utils.getCurrentBranch()
    return find_merge_request_id_by_branch(branch_to_find)


def find_merge_request_id_by_branch(branch_name):
    return gitlab_api.getMergeRequestForBranch(get_project_id(), branch_name)['iid']
