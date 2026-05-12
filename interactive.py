"""User prompts and CLI interactions."""
import datetime

import inquirer

import config
import gitlab_api


def enter_project_id():
    while True:
        project_id = input('Please enter the ID of your GitLab project: ')
        if project_id:
            return project_id
        exit('Invalid project ID.')


def select_milestone(milestones):
    titles = [t['title'] for t in milestones]
    questions = [inquirer.List('milestones', message="Select milestone:", choices=titles)]
    answer = inquirer.prompt(questions)
    return answer['milestones']


def get_selected_milestone(milestone_title, milestones):
    return next((t for t in milestones if t['title'] == milestone_title), None)


def get_milestone(manual):
    if manual:
        milestones = gitlab_api.list_milestones()
        return get_selected_milestone(select_milestone(milestones), milestones)

    milestones = gitlab_api.list_milestones()
    today = datetime.date.today().strftime('%Y-%m-%d')
    active = [
        m for m in milestones
        if m.get('start_date') and m.get('due_date')
        and m['start_date'] <= today <= m['due_date']
    ]
    active.sort(key=lambda x: x['due_date'])
    return active[0] if active else None


def select_iteration(iterations):
    choices = [t['start_date'] + ' - ' + t['due_date'] for t in iterations]
    questions = [inquirer.List('iterations', message="Select iteration:", choices=choices)]
    answer = inquirer.prompt(questions)
    return answer['iterations']


def get_selected_iteration(iteration_label, iterations):
    return next(
        (t for t in iterations if t['start_date'] + ' - ' + t['due_date'] == iteration_label),
        None,
    )


def get_active_iteration():
    iterations = gitlab_api.list_iterations()
    today = datetime.date.today().strftime('%Y-%m-%d')
    active = [
        i for i in iterations
        if i.get('start_date') and i.get('due_date')
        and i['start_date'] <= today <= i['due_date']
    ]
    active.sort(key=lambda x: x['due_date'])
    return active[0] if active else None


def get_iteration(manual):
    if manual:
        iterations = gitlab_api.list_iterations()
        return get_selected_iteration(select_iteration(iterations), iterations)
    return get_active_iteration()


def select_epic(epics):
    titles = [t['title'] for t in epics]
    search_query = inquirer.prompt([
        inquirer.Text('search_query', message='Search epic:'),
    ])['search_query']

    filtered = [c for c in titles if search_query.lower() in c.lower()]
    questions = [inquirer.List('epics', message="Select epic:", choices=filtered)]
    answer = inquirer.prompt(questions)
    return answer['epics']


def get_selected_epic(epic_title, epics):
    return next((t for t in epics if t['title'] == epic_title), None)


def get_epic():
    epics = gitlab_api.list_epics()
    return get_selected_epic(select_epic(epics), epics)


def choose_reviewers_manually():
    """Prompt the user to select reviewers from the configured reviewer list."""
    reviewer_choices = []
    for reviewer_id in config.REVIEWERS:
        user = gitlab_api.get_user(reviewer_id)
        if user:
            display_name = f"{user.get('name')} ({user.get('username')})"
            reviewer_choices.append((display_name, reviewer_id))
        else:
            reviewer_choices.append((str(reviewer_id), reviewer_id))

    questions = [
        inquirer.Checkbox(
            "selected_reviewers",
            message="Select reviewers",
            choices=[(name, str(rid)) for name, rid in reviewer_choices],
        ),
    ]
    answers = inquirer.prompt(questions)
    if answers and "selected_reviewers" in answers:
        return [int(r) for r in answers["selected_reviewers"]]
    return []


def select_labels(search, multiple=False):
    labels = gitlab_api.get_labels_of_group(search)
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


def prompt_estimated_time():
    return inquirer.prompt([
        inquirer.Text(
            'estimated_time',
            message='Estimated time to complete this issue (in minutes, optional)',
            validate=lambda _, x: x == '' or x.isdigit(),
        ),
    ])['estimated_time']


def prompt_spent_time():
    return inquirer.prompt([
        inquirer.Text(
            'spent_time',
            message='How many minutes did you actually spend on this issue?',
            validate=lambda _, x: x.isdigit(),
        ),
    ])['spent_time']
