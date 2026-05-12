import argparse
import sys

from .config import load_context
from . import gitlab_api, interactive, templates
from .commands import deploy, issues, open_mr, report, review, summary


def build_parser():
    parser = argparse.ArgumentParser("Argument description of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument("--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument(
        "-m",
        "--milestone",
        action="store_true",
        help="Add this flag, if you want to manually select milestone",
    )
    parser.add_argument(
        "--no_epic",
        action="store_true",
        help="Add this flag if you don't want to pick epic",
    )
    parser.add_argument(
        "--no_milestone",
        action="store_true",
        help="Add this flag if you don't want to pick milestone",
    )
    parser.add_argument(
        "--no_iteration",
        action="store_true",
        help="Add this flag if you don't want to pick iteration",
    )
    parser.add_argument(
        "--only_issue",
        action="store_true",
        help="Add this flag if you don't want to create merge request and branch alongside issue",
    )
    parser.add_argument(
        "-am",
        "--auto_merge",
        action="store_true",
        help="Add this flag to review if you want to set merge request to auto merge when pipeline succeeds",
    )
    parser.add_argument(
        "--select",
        action="store_true",
        help="Manually select reviewers for merge request (interactive)",
    )
    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    if not argv:
        parser.print_help()
        raise SystemExit(1)

    if any(arg in ("-h", "--help") for arg in argv):
        parser.parse_args(argv)
        return

    try:
        ctx = load_context()
    except RuntimeError as exc:
        print(exc)
        raise SystemExit(1) from exc

    args = parser.parse_args(argv)
    title = " ".join(args.title)

    if args.title[0] == "report":
        if len(args.title) != 3:
            print('Invalid report format. Use: gh report "text" minutes')
            return
        try:
            report.process_report(ctx, args.title[1], int(args.title[2].strip()))
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    if title == "open":
        open_mr.open_merge_request_in_browser(ctx)
        return
    if title == "review":
        review.review_current_merge_request(
            ctx, select_reviewers=args.select, auto_merge=args.auto_merge
        )
        return
    if title == "summary":
        summary.print_commit_summary(ctx)
        return
    if title == "summaryAI":
        summary.generate_smart_summary(ctx)
        return
    if title == "last deploy":
        deploy.get_last_production_deploy(ctx)
        return
    if title == "ai review":
        from ai_code_review import run_review

        run_review()
        return

    selected_settings = templates.get_issue_settings(
        ctx, interactive.select_template(ctx)
    )

    if not len(selected_settings):
        print("Custom selection of issue settings is not supported yet")

    if args.project_id and selected_settings.get("projectIds"):
        print("NOTE: Overwriting project id from argument...")

    project_id = (
        selected_settings.get("projectIds") or args.project_id or gitlab_api.get_project_id(ctx)
    )

    milestone = False
    if not args.no_milestone:
        milestone = interactive.get_milestone(ctx, args.milestone)["id"]

    iteration = False
    if not args.no_iteration:
        iteration = interactive.get_iteration(ctx, True)

    epic = False
    if not args.no_epic:
        epic = interactive.get_epic(ctx)

    issues.resolve_main_branch(ctx)
    only_issue = selected_settings.get("onlyIssue") or args.only_issue

    if isinstance(project_id, list):
        for selected_project_id in project_id:
            issues.start_issue_creation(
                ctx,
                selected_project_id,
                title,
                milestone,
                epic,
                iteration,
                selected_settings,
                only_issue,
            )
    else:
        issues.start_issue_creation(
            ctx,
            project_id,
            title,
            milestone,
            epic,
            iteration,
            selected_settings,
            only_issue,
        )
