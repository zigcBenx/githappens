from __future__ import annotations

from githappens.config import AppConfig
from githappens.gitlab_api import GitLabApi
from githappens.interactive import choose_reviewers_manually, prompt_spent_time
from githappens.commands.create_issue import resolve_project_id
from githappens.commands.open_mr import get_active_merge_request_id, get_merge_request_for_branch
from githappens import git_utils


def get_current_issue_id(api: GitLabApi) -> str:
    merge_request = get_merge_request_for_branch(api, git_utils.get_current_branch())
    if not merge_request:
        raise RuntimeError("No active merge request found for the current branch.")
    return merge_request["description"].replace('"', "").replace("#", "").split()[1]


def track_issue_time(api: GitLabApi) -> None:
    try:
        project_id = resolve_project_id(api)
        issue_id = get_current_issue_id(api)
    except Exception as error:
        print(f"Error getting issue details: {error}")
        return

    spent_time = int(prompt_spent_time())
    result = api.add_issue_note(project_id, issue_id, f"/spend {spent_time}m")
    if result.returncode == 0:
        print(f"Added {spent_time} minutes to issue {issue_id} time tracking.")
    else:
        print(f"Error adding time tracking: {result.stderr.decode().strip()}")


def add_reviewers_to_merge_request(config: AppConfig, api: GitLabApi, reviewers: list[int] | None = None) -> None:
    api.update_merge_request_reviewers(
        resolve_project_id(api),
        get_active_merge_request_id(api),
        reviewers if reviewers is not None else config.reviewers,
    )


def set_merge_request_to_auto_merge(api: GitLabApi) -> None:
    api.set_merge_request_auto_merge(resolve_project_id(api), get_active_merge_request_id(api))


def run_review_command(config: AppConfig, api: GitLabApi, select_reviewers: bool, auto_merge: bool) -> None:
    track_issue_time(api)
    reviewers = choose_reviewers_manually(config, api) if select_reviewers else None
    add_reviewers_to_merge_request(config, api, reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = resolve_project_id(api)
        run_review_for_mr(project_id, get_active_merge_request_id(api), config.gitlab_token, config.api_url)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        set_merge_request_to_auto_merge(api)
