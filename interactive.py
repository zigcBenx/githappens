#!/usr/bin/env python3
import inquirer

import config
import gitlab_api


def select_milestone(milestones):
    milestone_titles = [t['title'] for t in milestones]
    questions = [
        inquirer.List('milestones',
                      message="Select milestone:",
                      choices=milestone_titles),
    ]
    answer = inquirer.prompt(questions)
    return answer['milestones']


def get_selected_milestone(title, milestones):
    return next((t for t in milestones if t['title'] == title), None)


def get_milestone(manual=False):
    if manual:
        milestones = gitlab_api.list_milestones()
        return get_selected_milestone(select_milestone(milestones), milestones)
    return gitlab_api.list_milestones(current=True)


def select_iteration(iterations):
    iteration_labels = [t['start_date'] + ' - ' + t['due_date'] for t in iterations]
    questions = [
        inquirer.List('iterations',
                      message="Select iteration:",
                      choices=iteration_labels),
    ]
    answer = inquirer.prompt(questions)
    return answer['iterations']


def get_selected_iteration(label, iterations):
    return next((t for t in iterations if t['start_date'] + ' - ' + t['due_date'] == label), None)


def get_iteration(manual=False):
    if manual:
        iterations = gitlab_api.list_iterations()
        return get_selected_iteration(select_iteration(iterations), iterations)
    return gitlab_api.get_active_iteration()


def select_epic(epics):
    epic_titles = [t['title'] for t in epics]
    search_query = inquirer.prompt([
        inquirer.Text('search_query', message='Search epic:'),
    ])['search_query']

    filtered_epics = [c for c in epic_titles if search_query.lower() in c.lower()]
    questions = [
        inquirer.List('epics',
                      message="Select epic:",
                      choices=filtered_epics),
    ]
    answer = inquirer.prompt(questions)
    return answer['epics']


def get_selected_epic(title, epics):
    return next((t for t in epics if t['title'] == title), None)


def get_epic():
    epics = gitlab_api.list_epics()
    return get_selected_epic(select_epic(epics), epics)


def choose_reviewers_manually():
    reviewer_choices = []
    for reviewer_id in config.REVIEWERS:
        user = gitlab_api.get_user_details(reviewer_id)
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
        )
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
        inquirer.Text('estimated_time',
                      message='Estimated time to complete this issue (in minutes, optional)',
                      validate=lambda _, x: x == '' or x.isdigit())
    ])['estimated_time']


def prompt_spent_time():
    return inquirer.prompt([
        inquirer.Text('spent_time',
                      message='How many minutes did you actually spend on this issue?',
                      validate=lambda _, x: x.isdigit())
    ])['spent_time']
