import inquirer

from config import REVIEWERS
from gitlab_api import getLabelsOfGroup, get_user


def enterProjectId():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        exit("Invalid project ID.")


def select_milestone(milestones):
    choices = [milestone["title"] for milestone in milestones]
    questions = [
        inquirer.List(
            "milestones",
            message="Select milestone:",
            choices=choices,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["milestones"]


def getSelectedMilestone(milestone, milestones):
    return next((item for item in milestones if item["title"] == milestone), None)


def getSelectedIteration(iteration, iterations):
    return next(
        (
            item
            for item in iterations
            if item["start_date"] + " - " + item["due_date"] == iteration
        ),
        None,
    )


def select_iteration(iterations):
    choices = [item["start_date"] + " - " + item["due_date"] for item in iterations]
    questions = [
        inquirer.List(
            "iterations",
            message="Select iteration:",
            choices=choices,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["iterations"]


def select_epic(epics):
    epic_titles = [epic["title"] for epic in epics]
    search_query = inquirer.prompt(
        [inquirer.Text("search_query", message="Search epic:")]
    )["search_query"]

    filtered_epics = [
        choice for choice in epic_titles if search_query.lower() in choice.lower()
    ]
    questions = [
        inquirer.List(
            "epics",
            message="Select epic:",
            choices=filtered_epics,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["epics"]


def getSelectedEpic(epic, epics):
    return next((item for item in epics if item["title"] == epic), None)


def chooseReviewersManually():
    reviewer_choices = []
    for reviewer_id in REVIEWERS:
        user = get_user(reviewer_id)
        if user:
            display_name = f"{user.get('name')} ({user.get('username')})"
            reviewer_choices.append((display_name, reviewer_id))
        else:
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


def selectLabels(search, multiple=False):
    labels = getLabelsOfGroup(search)
    choices = sorted([label["name"] for label in labels])
    question_type = inquirer.Checkbox if multiple else inquirer.List
    questions = [
        question_type(
            "labels",
            message="Select one or more department labels:",
            choices=choices,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["labels"]
