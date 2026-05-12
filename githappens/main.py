import argparse
import sys

from . import config as settings
from . import git_utils
from .commands import deploy, open_mr, report, review, summary
from .commands.create_issue import get_project_id, start_issue_creation
from .interactive import choose_reviewers_manually, get_epic, get_iteration, get_milestone
from .templates import get_issue_settings, select_template


def main():
    parser = argparse.ArgumentParser("Argument description of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument("--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument("-m", "--milestone", action="store_true", help="Add this flag, if you want to manually select milestone")
    parser.add_argument("--no_epic", action="store_true", help="Add this flag if you don't want to pick epic")
    parser.add_argument("--no_milestone", action="store_true", help="Add this flag if you don't want to pick milestone")
    parser.add_argument("--no_iteration", action="store_true", help="Add this flag if you don't want to pick iteration")
    parser.add_argument("--only_issue", action="store_true", help="Add this flag if you don't want to create merge request and branch alongside issue")
    parser.add_argument("-am", "--auto_merge", action="store_true", help="Add this flag to review if you want to set merge request to auto merge when pipeline succeeds")
    parser.add_argument("--select", action="store_true", help="Manually select reviewers for merge request (interactive)")

    if len(sys.argv) <= 1:
        parser.print_help()
        raise SystemExit(1)

    args = parser.parse_args()
    if args.title[0] == "report":
        if len(args.title) != 3:
            print('Invalid report format. Use: gh report "text" minutes')
            return

        try:
            report.process_report(args.title[1], int(args.title[2].strip()))
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    title = " ".join(args.title)

    if title == "open":
        open_mr.open_merge_request_in_browser()
        return
    if title == "review":
        review.track_issue_time()
        reviewers = choose_reviewers_manually() if getattr(args, "select", False) else None
        review.add_reviewers_to_merge_request(reviewers=reviewers)

        try:
            from ai_code_review import run_review_for_mr

            project_id = get_project_id()
            mr_id = open_mr.get_active_merge_request_id()
            run_review_for_mr(project_id, mr_id, settings.GITLAB_TOKEN, settings.API_URL)
        except Exception as exc:
            print(f"AI review skipped: {exc}")

        if args.auto_merge:
            review.set_merge_request_to_auto_merge()
        return
    if title == "summary":
        git_utils.get_two_weeks_commits()
        return
    if title == "summaryAI":
        summary.generate_smart_summary()
        return
    if title == "last deploy":
        deploy.get_last_production_deploy()
        return
    if title == "ai review":
        from ai_code_review import run_review

        run_review()
        return

    selected_settings = get_issue_settings(select_template())
    if not len(selected_settings):
        print("Custom selection of issue settings is not supported yet")

    if args.project_id and selected_settings.get("projectIds"):
        print("NOTE: Overwriting project id from argument...")

    project_id = selected_settings.get("projectIds") or args.project_id or get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = get_milestone(args.milestone)["id"]

    iteration = False
    if not args.no_iteration:
        iteration = get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = get_epic()

    settings.MAIN_BRANCH = git_utils.get_main_branch()
    only_issue = selected_settings.get("onlyIssue") or args.only_issue

    if isinstance(project_id, list):
        for item_id in project_id:
            start_issue_creation(item_id, title, milestone, epic, iteration, selected_settings, only_issue)
    else:
        start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue)


if __name__ == "__main__":
    main()
