#!/usr/bin/env python3
import argparse
import sys

import git_utils
import interactive
from commands.create_issue import get_epic, get_iteration, get_milestone, process_report, start_issue_creation
from commands.deploy import get_last_production_deploy
from commands.open_mr import open_merge_request_in_browser
from commands.review import run_review_command
from config import OPENAI_API_KEY
from templates import get_issue_settings


def generate_smart_summary():
    commits = git_utils.get_two_weeks_commits(return_output=True)
    if not commits:
        return

    if not OPENAI_API_KEY:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Please install it using: pip install openai")
        return

    openai.api_key = OPENAI_API_KEY

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes git commits. Provide a concise, well-organized summary of the main changes and themes.",
                },
                {"role": "user", "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}"},
            ],
        )

        print("\nAI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating AI summary: {e}")


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
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()

    if len(argv) <= 0:
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
        open_merge_request_in_browser()
        return
    if title == "review":
        run_review_command(select=getattr(args, "select", False), auto_merge=args.auto_merge)
        return
    if title == "summary":
        git_utils.get_two_weeks_commits()
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

    selected_settings = get_issue_settings(interactive.select_template())

    if not len(selected_settings):
        print("Custom selection of issue settings is not supported yet")

    if args.project_id and selected_settings.get("projectIds"):
        print("NOTE: Overwriting project id from argument...")

    project_id = selected_settings.get("projectIds") or args.project_id or git_utils.resolve_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = get_milestone(args.milestone)["id"]

    iteration = False
    if not args.no_iteration:
        iteration = get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = get_epic()

    main_branch = git_utils.get_main_branch()
    only_issue = selected_settings.get("onlyIssue") or args.only_issue

    if type(project_id) == list:
        for project in project_id:
            start_issue_creation(project, title, milestone, epic, iteration, selected_settings, only_issue, main_branch)
    else:
        start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue, main_branch)


if __name__ == "__main__":
    main()
