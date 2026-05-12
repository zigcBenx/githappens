import datetime

import requests

from . import gitlab_api


def _inquirer():
    try:
        import inquirer
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency 'inquirer'. Run: pip install -r requirements.txt"
        ) from exc
    return inquirer


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        raise SystemExit("Invalid project ID.")


def select_template(ctx):
    inquirer = _inquirer()
    template_names = [template["name"] for template in ctx.templates]
    template_names.append(ctx.settings.custom_template)
    answer = inquirer.prompt(
        [
            inquirer.List(
                "template",
                message="Select template:",
                choices=template_names,
            )
        ]
    )
    return answer["template"]


def select_milestone(milestones):
    inquirer = _inquirer()
    choices = [milestone["title"] for milestone in milestones]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "milestones",
                message="Select milestone:",
                choices=choices,
            )
        ]
    )
    return answer["milestones"]


def get_selected_milestone(title, milestones):
    return next((milestone for milestone in milestones if milestone["title"] == title), None)


def get_milestone(ctx, manual):
    if manual:
        milestones = gitlab_api.list_milestones(ctx)
        return get_selected_milestone(select_milestone(milestones), milestones)
    return gitlab_api.list_milestones(ctx, current=True)


def select_iteration(iterations):
    inquirer = _inquirer()
    choices = [
        f"{iteration['start_date']} - {iteration['due_date']}" for iteration in iterations
    ]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "iterations",
                message="Select iteration:",
                choices=choices,
            )
        ]
    )
    return answer["iterations"]


def get_selected_iteration(iteration_label, iterations):
    return next(
        (
            iteration
            for iteration in iterations
            if f"{iteration['start_date']} - {iteration['due_date']}" == iteration_label
        ),
        None,
    )


def get_active_iteration(ctx):
    iterations = gitlab_api.list_iterations(ctx)
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = [
        iteration
        for iteration in iterations
        if iteration["start_date"]
        and iteration["due_date"]
        and iteration["start_date"] <= today <= iteration["due_date"]
    ]
    active_iterations.sort(key=lambda item: item["due_date"])
    return active_iterations[0]


def get_iteration(ctx, manual):
    if manual:
        iterations = gitlab_api.list_iterations(ctx)
        return get_selected_iteration(select_iteration(iterations), iterations)
    return get_active_iteration(ctx)


def select_epic(epics):
    inquirer = _inquirer()
    epic_titles = [epic["title"] for epic in epics]
    search_query = inquirer.prompt(
        [inquirer.Text("search_query", message="Search epic:")]
    )["search_query"]
    filtered_epics = [
        title for title in epic_titles if search_query.lower() in title.lower()
    ]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "epics",
                message="Select epic:",
                choices=filtered_epics,
            )
        ]
    )
    return answer["epics"]


def get_selected_epic(epic_title, epics):
    return next((epic for epic in epics if epic["title"] == epic_title), None)


def get_epic(ctx):
    epics = gitlab_api.list_epics(ctx)
    return get_selected_epic(select_epic(epics), epics)


def choose_reviewers_manually(ctx):
    """Prompt the user to select reviewers manually from configured reviewers."""
    inquirer = _inquirer()
    reviewer_choices = []
    for reviewer_id in ctx.reviewers:
        api_url = f"{ctx.settings.api_url}/users/{reviewer_id}"
        try:
            response = requests.get(
                api_url, headers=gitlab_api.private_token_headers(ctx)
            )
            if response.status_code == 200:
                user = response.json()
                display_name = f"{user.get('name')} ({user.get('username')})"
                reviewer_choices.append((display_name, str(reviewer_id)))
            else:
                reviewer_choices.append((str(reviewer_id), str(reviewer_id)))
        except Exception:
            reviewer_choices.append((str(reviewer_id), str(reviewer_id)))

    answers = inquirer.prompt(
        [
            inquirer.Checkbox(
                "selected_reviewers",
                message="Select reviewers",
                choices=reviewer_choices,
            )
        ]
    )
    if answers and "selected_reviewers" in answers:
        return [int(reviewer_id) for reviewer_id in answers["selected_reviewers"]]
    return []


def select_labels(ctx, search, multiple=False):
    inquirer = _inquirer()
    labels = gitlab_api.get_labels_of_group(ctx, search)
    choices = sorted([label["name"] for label in labels])
    question_type = inquirer.Checkbox if multiple else inquirer.List
    answer = inquirer.prompt(
        [
            question_type(
                "labels",
                message="Select one or more department labels:",
                choices=choices,
            )
        ]
    )
    return answer["labels"]
