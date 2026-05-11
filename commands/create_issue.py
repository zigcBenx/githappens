import gitlab_api as api
import interactive


def get_selected_milestone(milestone_title, milestones):
    return next((milestone for milestone in milestones if milestone["title"] == milestone_title), None)


def get_milestone(manual):
    if manual:
        milestones = api.list_milestones()
        return get_selected_milestone(interactive.select_milestone(milestones), milestones)
    return api.list_milestones(True)


def get_selected_iteration(iteration_title, iterations):
    return next(
        (
            iteration
            for iteration in iterations
            if f"{iteration['start_date']} - {iteration['due_date']}" == iteration_title
        ),
        None,
    )


def get_iteration(manual):
    if manual:
        iterations = api.list_iterations()
        return get_selected_iteration(interactive.select_iteration(iterations), iterations)
    return api.get_active_iteration()


def get_selected_epic(epic_title, epics):
    return next((epic for epic in epics if epic["title"] == epic_title), None)


def get_epic():
    epics = api.list_epics()
    return get_selected_epic(interactive.select_epic(epics), epics)


def start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue):
    estimated_time = interactive.prompt_estimated_time()
    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings["estimated_time"] = int(estimated_time_per_project)

    created_issue = api.create_issue(title, project_id, milestone, epic, iteration, selected_settings)
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = api.create_branch(project_id, created_issue)
    created_merge_request = api.create_merge_request(
        project_id,
        created_branch,
        created_issue,
        selected_settings.get("labels"),
        milestone,
    )
    print(f"Merge request #{created_merge_request['iid']}: {created_merge_request['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(f"         git checkout -b '{created_merge_request['source_branch']}' 'origin/{created_merge_request['source_branch']}'")
    print("to switch to new branch.")
    return created_issue
