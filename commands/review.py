#!/usr/bin/env python3
import config
import gitlab_api
import git_utils
import interactive


def run(auto_merge=False, select_reviewers=False):
    project_id = gitlab_api.get_project_id()
    mr = gitlab_api.get_merge_request_for_branch(git_utils.get_current_branch())
    if not mr:
        print("No active merge request found for current branch.")
        return

    issue_id = mr['description'].replace('"', '').replace('#', '').split()[1]
    spent_time = interactive.prompt_spent_time()
    gitlab_api.track_issue_time(project_id, issue_id, spent_time)

    reviewers = None
    if select_reviewers:
        reviewers = interactive.choose_reviewers_manually()
    gitlab_api.add_reviewers_to_merge_request(reviewers=reviewers)

    # Run AI code review and post to MR
    try:
        from ai_code_review import run_review_for_mr
        mr_id = gitlab_api.get_active_merge_request_id()
        run_review_for_mr(project_id, mr_id)
    except Exception as e:
        print(f"AI review skipped: {e}")

    if auto_merge:
        gitlab_api.set_merge_request_to_auto_merge()
