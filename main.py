import argparse
import sys

from config import MAIN_BRANCH, GITLAB_TOKEN, API_URL
from git_utils import getMainBranch, get_two_weeks_commits
from gitlab_api import get_project_id, addReviewersToMergeRequest, setMergeRequestToAutoMerge, getActiveMergeRequestId
from interactive import select_template, getIssueSettings, get_milestone, get_iteration, get_epic, chooseReviewersManually
from commands.create_issue import startIssueCreation
from commands.open_mr import openMergeRequestInBrowser
from commands.review import track_issue_time
from commands.deploy import process_report
from commands.summary import generate_smart_summary


def main():
    # global MAIN_BRANCH handled by config module

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
            process_report(text, minutes)
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    # So it takes all text until first known argument
    title = " ".join(args.title)

    if title == 'open':
        openMergeRequestInBrowser()
        return
    elif title == 'review':
        track_issue_time()
        reviewers = None
        if getattr(args, "select", False):
            reviewers = chooseReviewersManually()
        addReviewersToMergeRequest(reviewers=reviewers)

        # Run AI code review and post to MR
        try:
            from ai_code_review import run_review_for_mr
            project_id = get_project_id()
            mr_id = getActiveMergeRequestId()
            run_review_for_mr(project_id, mr_id, GITLAB_TOKEN, API_URL)
        except Exception as e:
            print(f"AI review skipped: {e}")

        if(args.auto_merge):
            setMergeRequestToAutoMerge()
        return
    elif title == 'summary':
        get_two_weeks_commits()
        return
    elif title == 'summaryAI':
        generate_smart_summary()
        return
    elif title == 'last deploy':
        get_last_production_deploy()
        return
    elif title == 'ai review':
        from ai_code_review import run_review
        run_review()
        return

    # Get settings for issue from template
    selectedSettings = getIssueSettings(select_template())

    # If template is False, ask for each settings
    if not len(selectedSettings):
        print('Custom selection of issue settings is not supported yet')
        pass

    if args.project_id and selectedSettings.get('projectIds'):
        print('NOTE: Overwriting project id from argument...')

    project_id = selectedSettings.get('projectIds') or args.project_id or get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = get_milestone(args.milestone)['id']

    iteration = False
    if not args.no_iteration:
        # manual pick iteration
        iteration = get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = get_epic()

    from config import MAIN_BRANCH as GLOBAL_MAIN_BRANCH
    GLOBAL_MAIN_BRANCH = getMainBranch()

    onlyIssue = selectedSettings.get('onlyIssue') or args.only_issue

    if type(project_id) == list:
        for id in project_id:
            startIssueCreation(id, title, milestone, epic, iteration, selectedSettings, onlyIssue)
    else:
        startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue)