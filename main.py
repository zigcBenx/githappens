#!/usr/bin/env python3
"""Entry point and argument parsing for gitHappens."""
import argparse
import sys

import config
import git_utils
import interactive
import templates
from commands.create_issue import start_issue_creation
from commands.deploy import get_last_production_deploy
from commands.incident import process_report
from commands.open_mr import open_merge_request_in_browser
from commands.review import run_review
from commands.summary import generate_smart_summary, show_two_weeks_commits
from project import get_project_id


def _build_parser():
    parser = argparse.ArgumentParser("Argument description of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument("--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument("-m", "--milestone", action='store_true',
                        help="Add this flag, if you want to manually select milestone")
    parser.add_argument("--no_epic", action="store_true",
                        help="Add this flag if you don't want to pick epic")
    parser.add_argument("--no_milestone", action="store_true",
                        help="Add this flag if you don't want to pick milestone")
    parser.add_argument("--no_iteration", action="store_true",
                        help="Add this flag if you don't want to pick iteration")
    parser.add_argument("--only_issue", action="store_true",
                        help="Add this flag if you don't want to create merge request and branch alongside issue")
    parser.add_argument("-am", "--auto_merge", action="store_true",
                        help="Set merge request to auto merge when pipeline succeeds")
    parser.add_argument("--select", action="store_true",
                        help="Manually select reviewers for merge request (interactive)")
    return parser


def _handle_report(parts):
    if len(parts) != 3:
        print("Invalid report format. Use: gh report \"text\" minutes")
        return
    text = parts[1]
    try:
        minutes = int(parts[2].strip())
        process_report(text, minutes)
    except ValueError:
        print("Invalid minutes. Please provide a valid number.")


def _handle_subcommand(title, args):
    """Return True if a subcommand was handled."""
    if title == 'open':
        open_merge_request_in_browser()
        return True
    if title == 'review':
        run_review(auto_merge=args.auto_merge, manual_select=getattr(args, "select", False))
        return True
    if title == 'summary':
        show_two_weeks_commits()
        return True
    if title == 'summaryAI':
        generate_smart_summary()
        return True
    if title == 'last deploy':
        get_last_production_deploy()
        return True
    if title == 'ai review':
        from ai_code_review import run_review as run_ai_review
        run_ai_review()
        return True
    return False


def main():
    parser = _build_parser()
    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args()

    if args.title[0] == 'report':
        _handle_report(args.title)
        return

    title = " ".join(args.title)

    if _handle_subcommand(title, args):
        return

    selected_settings = templates.get_issue_settings(templates.select_template())
    if not len(selected_settings):
        print('Custom selection of issue settings is not supported yet')

    if args.project_id and selected_settings.get('projectIds'):
        print('NOTE: Overwriting project id from argument...')

    project_id = selected_settings.get('projectIds') or args.project_id or get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = interactive.get_milestone(args.milestone)['id']

    iteration = False
    if not args.no_iteration:
        iteration = interactive.get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = interactive.get_epic()

    config.set_main_branch(git_utils.get_main_branch())

    only_issue = selected_settings.get('onlyIssue') or args.only_issue

    if isinstance(project_id, list):
        for pid in project_id:
            start_issue_creation(pid, title, milestone, epic, iteration, selected_settings, only_issue)
    else:
        start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue)


if __name__ == '__main__':
    main()
