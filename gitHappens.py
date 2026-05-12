#!/usr/bin/env python3
import argparse
import sys

from commands.create_issue import (
    get_epic,
    get_iteration,
    get_milestone,
    get_project_id,
    process_report,
    startIssueCreation,
)
from commands.deploy import get_last_production_deploy
from commands.open_mr import openMergeRequestInBrowser
from commands.review import review_current_merge_request
from commands.summary import generate_smart_summary
from git_utils import getMainBranch, get_two_weeks_commits
from templates import getIssueSettings, select_template


def build_parser():
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


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()

    if not argv:
        parser.print_help()
        exit(1)

    args = parser.parse_args(argv)
    if args.title[0] == "report":
        parts = args.title
        if len(parts) != 3:
            print('Invalid report format. Use: gh report "text" minutes')
            return

        text = parts[1]
        try:
            minutes = int(parts[2].strip())
            process_report(text, minutes)
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    title = " ".join(args.title)

    if title == "open":
        openMergeRequestInBrowser()
        return
    if title == "review":
        review_current_merge_request(auto_merge=args.auto_merge, select=args.select)
        return
    if title == "summary":
        get_two_weeks_commits()
        return
    if title == "summaryAI":
        generate_smart_summary()
        return
    if title == "last deploy":
        get_last_production_deploy()
        return
    if title == "ai review":
        from ai_code_review import run_review

        run_review()
        return

    selectedSettings = getIssueSettings(select_template()) or {}

    if not len(selectedSettings):
        print("Custom selection of issue settings is not supported yet")

    if args.project_id and selectedSettings.get("projectIds"):
        print("NOTE: Overwriting project id from argument...")

    project_id = selectedSettings.get("projectIds") or args.project_id or get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = get_milestone(args.milestone)["id"]

    iteration = False
    if not args.no_iteration:
        iteration = get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = get_epic()

    main_branch = getMainBranch()
    onlyIssue = selectedSettings.get("onlyIssue") or args.only_issue

    if type(project_id) == list:
        for item_id in project_id:
            startIssueCreation(
                item_id,
                title,
                milestone,
                epic,
                iteration,
                selectedSettings,
                onlyIssue,
                main_branch,
            )
    else:
        startIssueCreation(
            project_id,
            title,
            milestone,
            epic,
            iteration,
            selectedSettings,
            onlyIssue,
            main_branch,
        )


if __name__ == "__main__":
    main()
