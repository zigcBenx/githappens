from __future__ import annotations

import argparse
import sys

from .commands.create_issue import start_issue_creation
from .commands.deploy import print_last_production_deploy
from .commands.open_mr import open_merge_request_in_browser
from .commands.report import process_report
from .commands.review import review_current_merge_request
from .commands.summary import generate_smart_summary, print_recent_commits
from .config import load_app_config
from .git_utils import get_main_branch
from .gitlab_api import get_epic, get_iteration, get_milestone, get_project_id
from .templates import get_issue_settings, select_template


def build_parser() -> argparse.ArgumentParser:
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
    return parser


def run(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not argv:
        parser.print_help()
        raise SystemExit(1)

    args = parser.parse_args(argv)
    config = load_app_config()
    title = " ".join(args.title)

    if args.title[0] == "report":
        parts = args.title
        if len(parts) != 3:
            print('Invalid report format. Use: gh report "text" minutes')
            return
        try:
            process_report(config, parts[1], int(parts[2].strip()))
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    if title == "open":
        open_merge_request_in_browser(config)
        return
    if title == "review":
        review_current_merge_request(config, auto_merge=args.auto_merge, select_reviewers=args.select)
        return
    if title == "summary":
        print_recent_commits(config)
        return
    if title == "summaryAI":
        generate_smart_summary(config)
        return
    if title == "last deploy":
        print_last_production_deploy(config)
        return
    if title == "ai review":
        from ai_code_review import run_review

        run_review()
        return

    selected_settings = get_issue_settings(config, select_template(config))
    if not selected_settings:
        print("Custom selection of issue settings is not supported yet")

    if args.project_id and selected_settings.get("projectIds"):
        print("NOTE: Overwriting project id from argument...")

    project_id = selected_settings.get("projectIds") or args.project_id or get_project_id(config)
    milestone = False if args.no_milestone else get_milestone(config, args.milestone)["id"]
    iteration = False if args.no_iteration else get_iteration(config, True)
    epic = False if args.no_epic else get_epic(config)
    config.main_branch = get_main_branch()
    only_issue = selected_settings.get("onlyIssue") or args.only_issue

    if isinstance(project_id, list):
        for single_project_id in project_id:
            start_issue_creation(config, single_project_id, title, milestone, epic, iteration, selected_settings, only_issue)
    else:
        start_issue_creation(config, project_id, title, milestone, epic, iteration, selected_settings, only_issue)


def main() -> None:
    run()


if __name__ == "__main__":
    main()
