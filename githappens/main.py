from __future__ import annotations

import argparse
import sys

from . import git_utils
from .commands.create_issue import (
    create_incident_report,
    get_selected_epic,
    get_selected_iteration,
    get_selected_milestone,
    resolve_project_id,
    start_issue_creation,
)
from .commands.deploy import get_last_production_deploy
from .commands.open_mr import open_merge_request_in_browser
from .commands.review import run_review_command
from .config import AppConfig, load_app_config
from .gitlab_api import GitLabApi
from .interactive import prompt_estimated_time, select_template
from .templates import get_issue_settings


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


def main(config: AppConfig | None = None) -> None:
    parser = build_parser()
    if len(sys.argv) <= 1:
        parser.print_help()
        raise SystemExit(1)

    args = parser.parse_args()
    config = config or load_app_config()
    api = GitLabApi(config)
    title = " ".join(args.title)

    if args.title[0] == "report":
        if len(args.title) != 3:
            print('Invalid report format. Use: gh report "text" minutes')
            return
        try:
            create_incident_report(config, api, args.title[1], int(args.title[2].strip()))
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    if title == "open":
        open_merge_request_in_browser(config, api)
        return
    if title == "review":
        run_review_command(config, api, args.select, args.auto_merge)
        return
    if title == "summary":
        commits = git_utils.get_two_weeks_commits(config.developer_email)
        print(commits if commits else "No commits found.")
        return
    if title == "summaryAI":
        generate_smart_summary(config)
        return
    if title == "last deploy":
        get_last_production_deploy(config, api)
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

    project_id = selected_settings.get("projectIds") or args.project_id or resolve_project_id(api)
    selected_milestone = None if args.no_milestone else get_selected_milestone(api, args.milestone)
    milestone = selected_milestone["id"] if selected_milestone else False
    iteration = False if args.no_iteration else get_selected_iteration(api, True)
    epic = False if args.no_epic else get_selected_epic(api)
    main_branch = git_utils.get_main_branch()
    only_issue = selected_settings.get("onlyIssue") or args.only_issue
    estimated_time = _prompt_estimated_time_per_project(project_id)

    if isinstance(project_id, list):
        for item in project_id:
            start_issue_creation(config, api, item, title, milestone, epic, iteration, selected_settings, only_issue, main_branch, estimated_time)
    else:
        start_issue_creation(config, api, project_id, title, milestone, epic, iteration, selected_settings, only_issue, main_branch, estimated_time)


def _prompt_estimated_time_per_project(project_id: str | int | list[str | int]) -> int | None:
    estimated_time = prompt_estimated_time()
    if not estimated_time:
        return None
    project_count = len(project_id) if isinstance(project_id, list) else 1
    return int(int(estimated_time) / project_count)


def generate_smart_summary(config: AppConfig) -> None:
    commits = git_utils.get_two_weeks_commits(config.developer_email)
    if not commits:
        return
    if not config.openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Please install it using: pip install openai")
        return

    openai.api_key = config.openai_api_key
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes git commits. Provide a concise, well-organized summary of the main changes and themes."},
                {"role": "user", "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}"},
            ],
        )
        print("\nAI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as error:
        print(f"Error generating AI summary: {error}")
