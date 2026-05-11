from __future__ import annotations

from .. import git_utils, gitlab_api, interactive
from ..config import AppConfig
from .open_mr import get_active_merge_request_id


def get_current_issue_id(config: AppConfig):
    project_id = interactive.get_project_id(config)
    mr = gitlab_api.get_merge_request_for_branch(config, project_id, git_utils.get_current_branch())
    return mr["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time(config: AppConfig):
    import inquirer

    try:
        project_id = interactive.get_project_id(config)
        issue_id = get_current_issue_id(config)
    except Exception as e:
        print(f"Error getting issue details: {str(e)}")
        return

    spent_time = inquirer.prompt(
        [
            inquirer.Text(
                "spent_time",
                message="How many minutes did you actually spend on this issue?",
                validate=lambda _, x: x.isdigit(),
            )
        ]
    )["spent_time"]
    try:
        gitlab_api.add_issue_note(project_id, issue_id, f"/spend {spent_time}m")
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    except Exception as e:
        print(f"Error tracking issue time: {str(e)}")


def run(config: AppConfig, args):
    track_issue_time(config)
    reviewers = interactive.choose_reviewers_manually(config) if getattr(args, "select", False) else None
    project_id = interactive.get_project_id(config)
    mr_id = get_active_merge_request_id(config)
    gitlab_api.add_reviewers_to_merge_request(config, project_id, mr_id, reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        run_review_for_mr(project_id, mr_id, config.gitlab_token, config.api_url)
    except Exception as e:
        print(f"AI review skipped: {e}")

    if args.auto_merge:
        gitlab_api.set_merge_request_to_auto_merge(config, project_id, mr_id)
