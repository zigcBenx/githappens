from .. import git_utils, gitlab_api, interactive


def create_issue(ctx, title, project_id, milestone_id, epic, iteration, settings):
    if settings:
        issue_type = settings.get("type") or "issue"
        return gitlab_api.execute_issue_create(
            ctx,
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
    raise SystemExit(2)


def start_issue_creation(
    ctx, project_id, title, milestone_id, epic, iteration, selected_settings, only_issue
):
    inquirer = interactive._inquirer()
    estimated_time = inquirer.prompt(
        [
            inquirer.Text(
                "estimated_time",
                message="Estimated time to complete this issue (in minutes, optional)",
                validate=lambda _, value: value == "" or value.isdigit(),
            )
        ]
    )["estimated_time"]

    if isinstance(project_id, list):
        estimated_time_per_project = (
            int(estimated_time) / len(project_id) if estimated_time else None
        )
    else:
        estimated_time_per_project = estimated_time

    if estimated_time_per_project:
        selected_settings = selected_settings.copy() if selected_settings else {}
        selected_settings["estimated_time"] = int(estimated_time_per_project)

    created_issue = create_issue(
        ctx,
        title,
        project_id,
        milestone_id,
        epic,
        iteration,
        selected_settings,
    )
    print(f"Issue #{created_issue['iid']}: {created_issue['title']} created.")

    if only_issue:
        return created_issue

    created_branch = gitlab_api.create_branch(ctx, project_id, created_issue)
    created_mr = gitlab_api.create_merge_request(
        ctx,
        project_id,
        created_branch,
        created_issue,
        selected_settings.get("labels"),
        milestone_id,
    )
    print(f"Merge request #{created_mr['iid']}: {created_mr['title']} created.")
    print("Run:")
    print("         git fetch origin")
    print(
        f"         git checkout -b '{created_mr['source_branch']}' "
        f"'origin/{created_mr['source_branch']}'"
    )
    print("to switch to new branch.")

    return created_issue


def resolve_main_branch(ctx):
    ctx.main_branch = git_utils.get_main_branch()
    return ctx.main_branch
