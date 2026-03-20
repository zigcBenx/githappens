import config
import gitlab_api
import interactive


def review_command(args):
    interactive.track_issue_time()
    project_id = interactive.get_project_id()
    mr_id = interactive.getActiveMergeRequestId()
    reviewers = None
    if getattr(args, "select", False):
        reviewers = interactive.chooseReviewersManually()
    gitlab_api.addReviewersToMergeRequest(project_id, mr_id, reviewers=reviewers)

    try:
        from commands.ai_review import run_review_for_mr
        run_review_for_mr(project_id, mr_id, config.GITLAB_TOKEN, config.API_URL)
    except Exception as e:
        print(f"AI review skipped: {e}")

    if args.auto_merge:
        gitlab_api.setMergeRequestToAutoMerge(project_id, mr_id)
