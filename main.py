#!/usr/bin/env python3
import argparse
import config
import git_utils
import templates
import interactive
import commands.create_issue
import commands.open_mr
import commands.review
import commands.deploy
import commands.report
import commands.summary
import sys


def main():
    parser = argparse.ArgumentParser("Argument description of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument(f"--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument("-m", "--milestone", action='store_true', help="Add this flag, if you want to manually select milestone")
    parser.add_argument("--no_epic", action="store_true", help="Add this flag if you don't want to pick epic")
    parser.add_argument("--no_milestone", action="store_true", help="Add this flag if you don't want to pick milestone")
    parser.add_argument("--no_iteration", action="store_true", help="Add this flag if you don't want to pick iteration")
    parser.add_argument("--only_issue", action="store_true", help="Add this flag if you don't want to create merge request and branch alongside issue")
    parser.add_argument("-am", "--auto_merge", action="store_true", help="Add this flag to review if you want to set merge request to auto merge when pipeline succeeds")
    parser.add_argument("--select", action="store_true", help="Manually select reviewers for merge request (interactive)")

    # If no arguments passed, show help
    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args()
    if args.title[0] == 'report':
        parts = args.title
        if len(parts) != 3:
            print("Invalid report format. Use: gh report \"text\" minutes")
            return

        text = parts[1]
        try:
            minutes = int(parts[2].strip())
            commands.report.process_report(text, minutes)
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    # So it takes all text until first known argument
    title = " ".join(args.title)

    if title == 'open':
        commands.open_mr.openMergeRequestInBrowser()
        return
    elif title == 'review':
        commands.review.review_command(args)
        return
    elif title == 'summary':
        commands.summary.get_two_weeks_commits()
        return
    elif title == 'summaryAI':
        commands.summary.generate_smart_summary()
        return
    elif title == 'last deploy':
        commands.deploy.get_last_production_deploy()
        return
    elif title == 'ai review':
        from commands.ai_review import run_review
        run_review()
        return

    # Get settings for issue from template
    selectedSettings = templates.getIssueSettings(templates.select_template())

    # If template is False, ask for each settings
    if not len(selectedSettings):
        print('Custom selection of issue settings is not supported yet')
        pass

    if args.project_id and selectedSettings.get('projectIds'):
        print('NOTE: Overwriting project id from argument...')

    project_id = selectedSettings.get('projectIds') or args.project_id or interactive.get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = interactive.get_milestone(args.milestone)['id']

    iteration = False
    if not args.no_iteration:
        # manual pick iteration
        iteration = interactive.get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = interactive.get_epic()

    config.set_main_branch(git_utils.getMainBranch())

    onlyIssue = selectedSettings.get('onlyIssue') or args.only_issue

    if type(project_id) == list:
        for id in project_id:
            commands.create_issue.startIssueCreation(id, title, milestone, epic, iteration, selectedSettings, onlyIssue)
    else:
        commands.create_issue.startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue)


if __name__ == '__main__':
    main()
