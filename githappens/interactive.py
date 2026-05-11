from typing import Dict, List


def _inquirer():
    import inquirer

    return inquirer


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        exit("Invalid project ID.")


def select_template(templates: List[Dict], custom_template: str):
    inquirer = _inquirer()
    template_names = [template["name"] for template in templates]
    template_names.append(custom_template)
    questions = [
        inquirer.List(
            "template",
            message="Select template:",
            choices=template_names,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["template"]


def select_milestone(milestones):
    inquirer = _inquirer()
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


def get_selected_milestone(milestone, milestones):
    return next((item for item in milestones if item["title"] == milestone), None)


def select_iteration(iterations):
    inquirer = _inquirer()
    choices = [iteration["start_date"] + " - " + iteration["due_date"] for iteration in iterations]
    questions = [
        inquirer.List(
            "iterations",
            message="Select iteration:",
            choices=choices,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer["iterations"]


def get_selected_iteration(iteration, iterations):
    return next((item for item in iterations if item["start_date"] + " - " + item["due_date"] == iteration), None)


def select_epic(epics):
    inquirer = _inquirer()
    epic_titles = [epic["title"] for epic in epics]
    search_query = inquirer.prompt([
        inquirer.Text("search_query", message="Search epic:"),
    ])["search_query"]

    filtered_epics = [choice for choice in epic_titles if search_query.lower() in choice.lower()]
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


def choose_reviewers_manually(reviewers, api_url, gitlab_token):
    inquirer = _inquirer()
    import requests

    reviewer_choices = []
    for reviewer_id in reviewers:
        url = f"{api_url}/users/{reviewer_id}"
        headers = {"Private-Token": gitlab_token}
        try:
            response = requests.get(url, headers=headers)
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


def select_label(labels, multiple=False):
    inquirer = _inquirer()
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


enterProjectId = enter_project_id
getSelectedMilestone = get_selected_milestone
getSelectedIteration = get_selected_iteration
getSelectedEpic = get_selected_epic
