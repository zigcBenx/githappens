import inquirer
import datetime
import requests

from config import get_config


def enter_project_id():
    while True:
        project_id = input('Please enter the ID of your GitLab project: ')
        if project_id:
            return project_id
        exit('Invalid project ID.')


def select_milestone(milestones):
    milestone_titles = [t['title'] for t in milestones]
    questions = [
        inquirer.List('milestones',
                      message="Select milestone:",
                      choices=milestone_titles,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['milestones']


def get_selected_milestone(milestone, milestones):
    return next((t for t in milestones if t['title'] == milestone), None)


def get_milestone(manual):
    from gitlab_api import list_milestones
    if manual:
        milestones = list_milestones()
        return get_selected_milestone(select_milestone(milestones), milestones)
    milestone = list_milestones(True)  # select active for today
    return milestone


def select_iteration(iterations):
    iteration_strings = [t['start_date'] + ' - ' + t['due_date'] for t in iterations]
    questions = [
        inquirer.List('iterations',
                      message="Select iteration:",
                      choices=iteration_strings,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['iterations']


def get_selected_iteration(iteration, iterations):
    return next((t for t in iterations if t['start_date'] + ' - ' + t['due_date'] == iteration), None)


def get_active_iteration():
    from gitlab_api import list_iterations
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


def get_iteration(manual):
    # imported here to avoid circular dependency
    from gitlab_api import list_iterations
    if manual:
        iterations = list_iterations()
        return get_selected_iteration(select_iteration(iterations), iterations)
    return get_active_iteration()


def select_epic(epics):
    """Prompt user to select an epic with search."""
    epic_titles = [t['title'] for t in epics]
    search_query = inquirer.prompt([
        inquirer.Text('search_query', message='Search epic:'),
    ])['search_query']
    
    # Filter choices based on search query
    filtered_epics = [c for c in epic_titles if search_query.lower() in c.lower()]
    questions = [
        inquirer.List('epics',
                      message="Select epic:",
                      choices=filtered_epics,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['epics']


def get_selected_epic(epic, epics):
    return next((t for t in epics if t['title'] == epic), None)


def get_epic():
    from gitlab_api import list_epics
    epics = list_epics()
    return get_selected_epic(select_epic(epics), epics)


def choose_reviewers_manually():
    config = get_config()
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


def select_labels(search, multiple=False):
    from gitlab_api import get_labels_of_group
    labels = get_labels_of_group(search)
    label_names = sorted([t['name'] for t in labels])
    
    question_type = inquirer.Checkbox if multiple else inquirer.List
    questions = [
        question_type(
            'labels',
            message="Select one or more department labels:",
            choices=label_names,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer['labels']

