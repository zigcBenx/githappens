from .. import gitlab_api
from .. import interactive


def get_milestone(manual):
    if manual:
        milestones = gitlab_api.list_milestones()
        return interactive.get_selected_milestone(interactive.select_milestone(milestones), milestones)
    return gitlab_api.list_milestones(True)


def get_iteration(manual):
    if manual:
        iterations = gitlab_api.list_iterations()
        return interactive.get_selected_iteration(interactive.select_iteration(iterations), iterations)
    return gitlab_api.get_active_iteration()


def get_epic():
    epics = gitlab_api.list_epics()
    return interactive.get_selected_epic(interactive.select_epic(epics), epics)


def start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue, main_branch):
    import inquirer

    estimated_time = inquirer.prompt([
        inquirer.Text(
            "estimated_time",
            message="Estimated time to complete this issue (in minutes, optional)",
            validate=lambda _, value: value == "" or value.isdigit(),
        )
    ])["estimated_time"]

    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings["estimated_time"] = int(estimated_time_per_project)

    created_issue = gitlab_api.create_issue(title, project_id, milestone, epic, iteration, selected_settings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = gitlab_api.create_branch(project_id, created_issue, main_branch)
    created_merge_request = gitlab_api.create_merge_request(
        project_id,
        created_branch,
        created_issue,
        selected_settings.get("labels"),
        milestone,
        main_branch,
    )
    print(f"Merge request #{created_merge_request['iid']}: {created_merge_request['title']} created.")

    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_merge_request['source_branch']}' 'origin/{created_merge_request['source_branch']}'")
    print("to switch to new branch.")

    return created_issue


startIssueCreation = start_issue_creation
