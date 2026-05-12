#!/usr/bin/env python3
import argparse
import sys

import config
import gitlab_api
import git_utils
import interactive
import templates
from commands import create_issue, review, open_mr, deploy, report, summary, ai_review

_parser = argparse.ArgumentParser("Argument description of Git happens")
_parser.add_argument("title", nargs="+", help="Title of issue")
_parser.add_argument("--project_id", type=str, help="Id or URL-encoded path of project")
_parser.add_argument("-m", "--milestone", action='store_true', help="Add this flag, if you want to manually select milestone")
_parser.add_argument("--no_epic", action="store_true", help="Add this flag if you don't want to pick epic")
_parser.add_argument("--no_milestone", action="store_true", help="Add this flag if you don't want to pick milestone")
_parser.add_argument("--no_iteration", action="store_true", help="Add this flag if you don't want to pick iteration")
_parser.add_argument("--only_issue", action="store_true", help="Add this flag if you don't want to create merge request and branch alongside issue")
_parser.add_argument("-am", "--auto_merge", action="store_true", help="Add this flag to review if you want to set merge request to auto merge when pipeline succeeds")
_parser.add_argument("--select", action="store_true", help="Manually select reviewers for merge request (interactive)")


def main():
    if len(sys.argv) <= 1:
        _parser.print_help()
        sys.exit(1)

    args = _parser.parse_args()

    if args.title[0] == 'report':
        parts = args.title
        if len(parts) != 3:
            print("Invalid report format. Use: gh report \"text\" minutes")
            return
        text = parts[1]
        try:
            minutes = int(parts[2].strip())
            report.run(text, minutes)
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    title = " ".join(args.title)

    if title == 'open':
        open_mr.run()
        return
    elif title == 'review':
        review.run(auto_merge=args.auto_merge, select_reviewers=args.select)
        return
    elif title == 'summary':
        summary.run(ai=False)
        return
    elif title == 'summaryAI':
        summary.run(ai=True)
        return
    elif title == 'last deploy':
        deploy.run()
        return
    elif title == 'ai review':
        ai_review.run()
        return

    selected_settings = templates.get_issue_settings(templates.select_template())

    if not len(selected_settings):
        print('Custom selection of issue settings is not supported yet')

    if args.project_id and selected_settings.get('projectIds'):
        print('NOTE: Overwriting project id from argument...')

    project_id = selected_settings.get('projectIds') or args.project_id or gitlab_api.get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = interactive.get_milestone(args.milestone)['id']

    iteration = False
    if not args.no_iteration:
        iteration = interactive.get_iteration(manual=True)

    epic = False
    if not args.no_epic:
        epic = interactive.get_epic()

    config.MAIN_BRANCH = git_utils.get_main_branch()

    only_issue = selected_settings.get('onlyIssue') or args.only_issue

    if isinstance(project_id, list):
        for pid in project_id:
            create_issue.run(title, pid, milestone, epic, iteration, selected_settings, only_issue)
    else:
        create_issue.run(title, project_id, milestone, epic, iteration, selected_settings, only_issue)


if __name__ == '__main__':
    main()
