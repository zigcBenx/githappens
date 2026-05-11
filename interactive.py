import inquirer

import config
import templates


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        exit("Invalid project ID.")


def select_template():
    template_names = [template["name"] for template in templates.TEMPLATES]
    template_names.append(config.CUSTOM_TEMPLATE)
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
    milestone_titles = [milestone["title"] for milestone in milestones]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "milestones",
                message="Select milestone:",
                choices=milestone_titles,
            )
        ]
    )
    return answer["milestones"]


def select_iteration(iterations):
    iteration_titles = [f"{iteration['start_date']} - {iteration['due_date']}" for iteration in iterations]
    answer = inquirer.prompt(
        [
            inquirer.List(
                "iterations",
                message="Select iteration:",
                choices=iteration_titles,
            )
        ]
    )
    return answer["iterations"]


def select_epic(epics):
    epic_titles = [epic["title"] for epic in epics]
    search_query = inquirer.prompt(
        [inquirer.Text("search_query", message="Search epic:")]
    )["search_query"]

    filtered_epics = [choice for choice in epic_titles if search_query.lower() in choice.lower()]
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


def prompt_estimated_time():
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
    return inquirer.prompt(
        [
            inquirer.Text(
                "spent_time",
                message="How many minutes did you actually spend on this issue?",
                validate=lambda _, value: value.isdigit(),
            )
        ]
    )["spent_time"]


def choose_reviewers_manually(reviewer_choices):
    answer = inquirer.prompt(
        [
            inquirer.Checkbox(
                "selected_reviewers",
                message="Select reviewers",
                choices=[(name, str(reviewer_id)) for name, reviewer_id in reviewer_choices],
            )
        ]
    )
    if answer and "selected_reviewers" in answer:
        return [int(reviewer) for reviewer in answer["selected_reviewers"]]
    return []


def select_labels(labels, multiple=False):
    question_type = inquirer.Checkbox if multiple else inquirer.List
    answer = inquirer.prompt(
        [
            question_type(
                "labels",
                message="Select one or more department labels:",
                choices=sorted(labels),
            )
        ]
    )
    return answer["labels"]
