import datetime
import json
import inquirer
import subprocess

from config import GROUP_ID, API_URL, GITLAB_TOKEN, CUSTOM_TEMPLATE
from templates import TEMPLATES, REVIEWERS
from gitlab_api import list_milestones, list_iterations, list_epics, getLabelsOfGroup, getAuthorizedUser


def enterProjectId():
    while True:
        project_id = input('Please enter the ID of your GitLab project: ')
        if project_id:
            return project_id
        exit('Invalid project ID.')

def select_template():
    template_names = [t['name'] for t in TEMPLATES]
    template_names.append(CUSTOM_TEMPLATE)
    questions = [
        inquirer.List('template',
                      message="Select template:",
                      choices=template_names,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['template']

def getIssueSettings(template_name):
    if template_name == CUSTOM_TEMPLATE:
        return {}
    return next((t for t in TEMPLATES if t['name'] == template_name), None)

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
        milestones = list_milestones()
        return getSelectedMilestone(select_milestone(milestones), milestones)
    milestone = list_milestones(True) # select active for today
    return milestone

def get_iteration(manual):
    if manual:
        iterations = list_iterations()
        return getSelectedIteration(select_iteration(iterations), iterations)
    return getActiveIteration()

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

def getActiveIteration():
    iterations = list_iterations()
    today = datetime.date.today().strftime('%Y-%m-%d')
    active_iterations = []
    for iteration in iterations:
        start_date = iteration['start_date']
        due_date = iteration['due_date']
        if start_date and due_date and start_date <= today and due_date >= today:
            active_iterations.append(iteration)
    active_iterations.sort(key=lambda x: x['due_date'])
    return active_iterations[0]

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
    epics = list_epics()
    return getSelectedEpic(select_epic(epics), epics)

def chooseReviewersManually():
    """Prompt the user to select reviewers manually from the available list, showing names."""
    # Fetch user details for each reviewer ID
    reviewer_choices = []
    for reviewer_id in REVIEWERS:
        api_url = f"{API_URL}/users/{reviewer_id}"
        headers = {"Private-Token": GITLAB_TOKEN}
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

def selectLabels(search, multiple = False):
    labels = getLabelsOfGroup(search)
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

