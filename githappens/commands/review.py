from __future__ import annotations

from ..config import AppConfig
from ..git_utils import get_current_branch
from ..gitlab_api import (
    add_reviewers_to_merge_request,
    find_merge_request_id_by_branch,
    get_project_id,
    get_user_details,
    set_merge_request_to_auto_merge,
    track_issue_time,
)
from ..interactive import choose_reviewers_manually


def review_current_merge_request(config: AppConfig, auto_merge: bool = False, select_reviewers: bool = False) -> None:
    track_issue_time(config)

    reviewers = None
    if select_reviewers:
        reviewers = choose_reviewers_manually(config, lambda reviewer_id: get_user_details(config, reviewer_id))

    add_reviewers_to_merge_request(config, reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        project_id = get_project_id(config)
        merge_request_id = find_merge_request_id_by_branch(config, get_current_branch())
        run_review_for_mr(project_id, merge_request_id, config.gitlab_token, config.api_url)
    except Exception as error:
        print(f"AI review skipped: {error}")

    if auto_merge:
        set_merge_request_to_auto_merge(config)
