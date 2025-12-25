#!/usr/bin/env python3
import argparse
import sys

from config import get_config
from templates import select_template
from gitlab_api import get_project_id
from git_utils import get_main_branch
from interactive import get_milestone, get_iteration, get_epic
from commands.create_issue import start_issue_creation
from commands.review import handle_review_command
from commands.deploy import handle_deploy_command
from commands.open_mr import handle_open_command
from commands.summary import handle_summary_command, handle_summary_ai_command
from commands.report import handle_report_command


def main():
    parser = argparse.ArgumentParser("Argument description of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument("--project_id", type=str, help="Id or URL-encoded path of project")
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
        handle_report_command(args.title)
        return
    
    # Takes all text until first known argument
    title = " ".join(args.title)
    
    if title == 'open':
        handle_open_command()
        return
    elif title == 'review':
        handle_review_command(args)
        return
    elif title == 'summary':
        handle_summary_command()
        return
    elif title == 'summaryAI':
        handle_summary_ai_command()
        return
    elif title == 'last deploy':
        handle_deploy_command()
        return
    elif title == 'ai review':
        from ai_code_review import run_review
        run_review()
        return
    
    # Handle issue creation workflow
    config = get_config()
    
    # Get settings for issue from template
    selected_settings = config.get_issue_settings(select_template())
    
    # If template is False, ask for each settings
    if not len(selected_settings):
        print('Custom selection of issue settings is not supported yet')
        pass
    
    if args.project_id and selected_settings.get('projectIds'):
        print('NOTE: Overwriting project id from argument...')
    
    project_id = selected_settings.get('projectIds') or args.project_id or get_project_id()
    
    milestone = False
    if not args.no_milestone:
        milestone_obj = get_milestone(args.milestone)
        milestone = milestone_obj['id'] if milestone_obj and milestone_obj.get('id') else False
    
    iteration = False
    if not args.no_iteration:
        # manual pick iteration
        iteration = get_iteration(True)
    
    epic = False
    if not args.no_epic:
        epic = get_epic()
    
    main_branch = get_main_branch()
    
    only_issue = selected_settings.get('onlyIssue') or args.only_issue
    
    if type(project_id) == list:
        for id in project_id:
            start_issue_creation(id, title, milestone, epic, iteration, selected_settings, only_issue)
    else:
        start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue)


if __name__ == '__main__':
    main()

