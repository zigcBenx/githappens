#!/usr/bin/env python3
"""GitHappens CLI – main entry point. Preserves exact original CLI behavior."""
import argparse
import sys
from config import get_project_id, get_main_branch, get_custom_template
from templates import select_template, getIssueSettings, select_epic, getSelectedEpic, chooseReviewersManually
from gitlab_api import (
    list_milestones, get_milestone,
    list_iterations, get_iteration,
    list_epics,
    getAuthorizedUser,
    addReviewersToMergeRequest, setMergeRequestToAutoMerge,
    getActiveMergeRequestId,
    get_last_production_deploy,
)
from interactive import startIssueCreation
from git_utils import (
    get_two_weeks_commits, generate_smart_summary,
    process_report, track_issue_time,
)


def openMergeRequestInBrowser():
    """Open the active merge request in the browser."""
    from config import get_base_url
    import webbrowser
    import subprocess
    try:
        mr_id = getActiveMergeRequestId()
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], text=True
        ).strip()
        url = get_base_url() + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{mr_id}")
    except subprocess.CalledProcessError:
        return None


def main():
    parser = argparse.ArgumentParser("GitHappens CLI")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument("--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument("-m", "--milestone", action='store_true', help="Manually select milestone")
    parser.add_argument("--no_epic", action="store_true", help="Skip epic selection")
    parser.add_argument("--no_milestone", action="store_true", help="Skip milestone selection")
    parser.add_argument("--no_iteration", action="store_true", help="Skip iteration selection")
    parser.add_argument("--only_issue", action="store_true", help="Create issue only, no MR")
    parser.add_argument("-am", "--auto_merge", action='store_true', help="Auto-merge MR when pipeline succeeds")
    parser.add_argument("--select", action='store_true', help="Manually select reviewers")

    if len(sys.argv) <= 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args()

    # 'report' subcommand
    if args.title[0] == 'report':
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

    if title == 'open':
        openMergeRequestInBrowser()
        return
    elif title == 'review':
        track_issue_time()
        reviewers = None
        if getattr(args, "select", False):
            reviewers = chooseReviewersManually()
        addReviewersToMergeRequest(reviewers=reviewers)
        try:
            from ai_code_review import run_review_for_mr
            from config import get_project_id as _gpid, get_gitlab_token, get_api_url
            project_id = _gpid()
            mr_id = getActiveMergeRequestId()
            run_review_for_mr(project_id, mr_id, get_gitlab_token(), get_api_url())
        except Exception as e:
            print(f"AI review skipped: {e}")
        if args.auto_merge:
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

    # Issue creation flow
    selectedSettings = getIssueSettings(select_template())
    if not selectedSettings:
        print("Custom selection of issue settings is not supported yet")
        return

    if args.project_id and selectedSettings.get('projectIds'):
        print("NOTE: Overwriting project id from argument...")

    project_id = selectedSettings.get('projectIds') or args.project_id or get_project_id()

    milestone = False
    if not args.no_milestone:
        m = get_milestone(args.milestone)
        milestone = m['id'] if m else False

    iteration = False
    if not args.no_iteration:
        iteration = get_iteration(True)

    epic = False
    if not args.no_epic:
        epics = list_epics()
        epic = getSelectedEpic(select_epic(epics), epics)

    main_branch = get_main_branch()
    onlyIssue = selectedSettings.get('onlyIssue') or args.only_issue

    if isinstance(project_id, list):
        for pid in project_id:
            startIssueCreation(pid, title, milestone, epic, iteration, selectedSettings, onlyIssue)
    else:
        startIssueCreation(project_id, title, milestone, epic, iteration, selectedSettings, onlyIssue)


if __name__ == "__main__":
    main()