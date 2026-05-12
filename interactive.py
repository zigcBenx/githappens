import requests

from config import CONFIG, REVIEWERS
from gitlab_api import (
    get_active_iteration,
    get_labels_of_group,
    list_epics,
    list_iterations,
    list_milestones,
)


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        exit("Invalid project ID.")


def select_milestone(milestones):
    import inquirer

    milestone_names = [milestone["title"] for milestone in milestones]
    questions = [
        inquirer.List(
            "milestones",
            message="Select milestone:",
            choices=milestone_names,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["milestones"]


def get_selected_milestone(milestone, milestones):
    return next((item for item in milestones if item["title"] == milestone), None)


def get_milestone(manual):
    if manual:
        milestones = list_milestones()
        return get_selected_milestone(select_milestone(milestones), milestones)
    return list_milestones(True)


def select_iteration(iterations):
    import inquirer

    iteration_names = [item["start_date"] + " - " + item["due_date"] for item in iterations]
    questions = [
        inquirer.List(
            "iterations",
            message="Select iteration:",
            choices=iteration_names,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["iterations"]


def get_selected_iteration(iteration, iterations):
    return next(
        (item for item in iterations if item["start_date"] + " - " + item["due_date"] == iteration),
        None,
    )


def get_iteration(manual):
    if manual:
        iterations = list_iterations()
        return get_selected_iteration(select_iteration(iterations), iterations)
    return get_active_iteration()


def select_epic(epics):
    import inquirer

    epic_names = [epic["title"] for epic in epics]
    search_query = inquirer.prompt(
        [inquirer.Text("search_query", message="Search epic:")]
    )["search_query"]
    filtered_epics = [choice for choice in epic_names if search_query.lower() in choice.lower()]
    questions = [
        inquirer.List(
            "epics",
            message="Select epic:",
            choices=filtered_epics,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["epics"]


def get_selected_epic(epic, epics):
    return next((item for item in epics if item["title"] == epic), None)


def get_epic():
    epics = list_epics()
    return get_selected_epic(select_epic(epics), epics)


def choose_reviewers_manually():
    import inquirer

    reviewer_choices = []
    for reviewer_id in REVIEWERS:
        api_url = f"{CONFIG.api_url}/users/{reviewer_id}"
        headers = {"Private-Token": CONFIG.gitlab_token}
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
            choices=[(name, str(reviewer_id)) for name, reviewer_id in reviewer_choices],
        )
    ]
    answers = inquirer.prompt(questions)
    if answers and "selected_reviewers" in answers:
        return [int(reviewer) for reviewer in answers["selected_reviewers"]]
    return []


def select_labels(search, multiple=False):
    import inquirer

    labels = get_labels_of_group(search)
    label_names = sorted([label["name"] for label in labels])
    question_type = inquirer.Checkbox if multiple else inquirer.List
    questions = [
        question_type(
            "labels",
            message="Select one or more department labels:",
            choices=label_names,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["labels"]


def prompt_estimated_time():
    import inquirer

    return inquirer.prompt(
        [
            inquirer.Text(
                "estimated_time",
                message="Estimated time to complete this issue (in minutes, optional)",
                validate=lambda _, value: value == "" or value.isdigit(),
            )
        ]
    )["estimated_time"]


def prompt_spent_time():
    import inquirer

    return inquirer.prompt(
        [
            inquirer.Text(
                "spent_time",
                message="How many minutes did you actually spend on this issue?",
                validate=lambda _, value: value.isdigit(),
            )
        ]
    )["spent_time"]


# Backwards-compatible names.
enterProjectId = enter_project_id
select_milestone = select_milestone
getSelectedMilestone = get_selected_milestone
get_milestone = get_milestone
select_iteration = select_iteration
getSelectedIteration = get_selected_iteration
get_iteration = get_iteration
select_epic = select_epic
getSelectedEpic = get_selected_epic
get_epic = get_epic
chooseReviewersManually = choose_reviewers_manually
selectLabels = select_labels
