import datetime

from .. import config, git_utils, gitlab_api, interactive


def get_project_id():
    project_link = git_utils.get_project_link_from_current_dir()
    if project_link == -1:
        return interactive.enter_project_id()

    all_projects = gitlab_api.get_all_projects(project_link)
    if all_projects is None:
        return None
    matching_id = None
    for project in all_projects:
        if project.get("ssh_url_to_repo") == project_link:
            matching_id = project.get("id")
            break
    return matching_id


def get_selected_milestone(milestone, milestones):
    return next((item for item in milestones if item["title"] == milestone), None)


def get_milestone(manual):
    if manual:
        milestones = gitlab_api.list_milestones()
        return get_selected_milestone(interactive.select_milestone(milestones), milestones)
    return gitlab_api.list_milestones(True)


def get_selected_iteration(iteration, iterations):
    return next(
        (
            item
            for item in iterations
            if item["start_date"] + " - " + item["due_date"] == iteration
        ),
        None,
    )


def get_active_iteration():
    iterations = gitlab_api.list_iterations()
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = []
    for iteration in iterations:
        start_date = iteration["start_date"]
        due_date = iteration["due_date"]
        if start_date and due_date and start_date <= today and due_date >= today:
            active_iterations.append(iteration)
    active_iterations.sort(key=lambda item: item["due_date"])
    if not active_iterations:
        return None
    return active_iterations[0]


def get_iteration(manual):
    if manual:
        iterations = gitlab_api.list_iterations()
        return get_selected_iteration(interactive.select_iteration(iterations), iterations)
    return get_active_iteration()


def get_selected_epic(epic, epics):
    return next((item for item in epics if item["title"] == epic), None)


def get_epic():
    epics = gitlab_api.list_epics()
    return get_selected_epic(interactive.select_epic(epics), epics)


def create_issue(title, project_id, milestone_id, epic, iteration, settings):
    if settings:
        issue_type = settings.get("type") or "issue"
        return gitlab_api.create_issue(
            project_id,
            title,
            settings.get("labels"),
            milestone_id,
            epic,
            iteration,
            settings.get("weight"),
            settings.get("estimated_time"),
            issue_type,
        )
    print("No settings in template")
    exit(2)


def start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue, main_branch):
    estimated_time = interactive.prompt_estimated_time()

    if isinstance(project_id, list):
        estimated_time_per_project = int(estimated_time) / len(project_id) if estimated_time else None
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings["estimated_time"] = int(estimated_time_per_project)

    created_issue = create_issue(title, project_id, milestone, epic, iteration, selected_settings)
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


def create_issue_flow(title, args, selected_settings):
    if args.project_id and selected_settings.get("projectIds"):
        print("NOTE: Overwriting project id from argument...")

    project_id = selected_settings.get("projectIds") or args.project_id or get_project_id()

    milestone = False
    if not args.no_milestone:
        selected_milestone = get_milestone(args.milestone)
        milestone = selected_milestone["id"] if selected_milestone else False

    iteration = False
    if not args.no_iteration:
        iteration = get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = get_epic()

    main_branch = git_utils.get_main_branch()
    only_issue = selected_settings.get("onlyIssue") or args.only_issue

    if type(project_id) == list:
        for project in project_id:
            start_issue_creation(project, title, milestone, epic, iteration, selected_settings, only_issue, main_branch)
    else:
        start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue, main_branch)


def select_labels(search, multiple=False):
    labels = gitlab_api.list_labels(search)
    return interactive.select_labels(labels, multiple)
