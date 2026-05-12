import subprocess

from .. import git_utils, gitlab_api, interactive
from .open_mr import get_active_merge_request_id


def get_current_issue_id(ctx):
    mr = gitlab_api.get_merge_request_for_branch(ctx, git_utils.get_current_branch())
    return mr["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time(ctx):
    try:
        project_id = gitlab_api.get_project_id(ctx)
        issue_id = get_current_issue_id(ctx)
    except Exception as exc:
        print(f"Error getting issue details: {str(exc)}")
        return

    inquirer = interactive._inquirer()
    spent_time = inquirer.prompt(
        [
            inquirer.Text(
                "spent_time",
                message="How many minutes did you actually spend on this issue?",
                validate=lambda _, value: value.isdigit(),
            )
        ]
    )["spent_time"]

    command = [
        "glab",
        "api",
        f"/projects/{project_id}/issues/{issue_id}/notes",
        "-f",
        f"body=/spend {spent_time}m",
    ]

    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except subprocess.CalledProcessError as exc:
        print(f"Error adding time tracking: {str(exc)}")
    except Exception as exc:
        print(f"Error tracking issue time: {str(exc)}")


def review_current_merge_request(ctx, select_reviewers=False, auto_merge=False):
    track_issue_time(ctx)
    reviewers = interactive.choose_reviewers_manually(ctx) if select_reviewers else None
    mr_id = get_active_merge_request_id(ctx)
    gitlab_api.add_reviewers_to_merge_request(ctx, mr_id, reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = gitlab_api.get_project_id(ctx)
        run_review_for_mr(
            project_id,
            mr_id,
            ctx.settings.gitlab_token,
            ctx.settings.api_url,
        )
    except Exception as exc:
        print(f"AI review skipped: {exc}")

    if auto_merge:
        gitlab_api.set_merge_request_to_auto_merge(ctx, mr_id)
