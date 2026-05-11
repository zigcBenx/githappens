from __future__ import annotations

import argparse
import sys

from githappens.commands.deploy import get_last_production_deploy
from githappens.commands.create_issue import (
    get_active_iteration,
    get_current_milestone,
    process_report,
    start_issue_creation,
)
from githappens.commands.open_mr import open_merge_request_in_browser
from githappens.commands.review import (
    add_reviewers_to_merge_request,
    get_merge_request_for_current_branch,
    set_merge_request_to_auto_merge,
    track_issue_time,
)
from githappens.commands.summary import generate_smart_summary, print_recent_commits
from githappens.git_utils import (
    enter_project_id,
    find_matching_project_id,
    get_main_branch,
    get_project_link_from_current_dir,
    get_project_search_term,
    get_two_weeks_commits,
)
from githappens.gitlab_api import GitLabApiError, GitLabClient
from githappens.interactive import (
    choose_reviewers_manually,
    select_epic,
    select_iteration,
    select_milestone,
    select_template,
)
from githappens.runtime import load_runtime
from githappens.templates import get_issue_settings, get_template_names


def _resolve_project_id(client: GitLabClient, explicit_project_id=None):
    if explicit_project_id:
        return explicit_project_id

    project_link = get_project_link_from_current_dir()
    if not project_link:
        return enter_project_id()

    projects = client.get_all_projects(get_project_search_term(project_link))
    project_id = find_matching_project_id(projects, project_link)
    return project_id or enter_project_id()


def _select_current_milestone(client: GitLabClient, manual: bool):
    if manual:
        milestones = client.list_milestones()
        selected_title = select_milestone(milestones)
        return next((milestone for milestone in milestones if milestone["title"] == selected_title), None)
    return get_current_milestone(client)


def _select_iteration(client: GitLabClient, manual: bool):
    if manual:
        iterations = client.list_iterations()
        selected_label = select_iteration(iterations)
        return next(
            (
                iteration
                for iteration in iterations
                if f"{iteration['start_date']} - {iteration['due_date']}" == selected_label
            ),
            None,
        )
    return get_active_iteration(client)


def _select_epic(client: GitLabClient):
    epics = client.list_epics()
    selected_title = select_epic(epics)
    return next((epic for epic in epics if epic["title"] == selected_title), None)


def _run_review(runtime, client, args, project_id):
    track_issue_time(client, project_id)

    reviewers = None
    if getattr(args, "select", False):
        reviewers = choose_reviewers_manually(client, runtime.reviewers)

    add_reviewers_to_merge_request(runtime, client, project_id, reviewers=reviewers)

    try:
        from ai_code_review import run_review_for_mr

        merge_request = get_merge_request_for_current_branch(client, project_id)
        run_review_for_mr(project_id, merge_request["iid"], runtime.config.gitlab_token, client.api_url)
    except Exception as exc:
        print(f"AI review skipped: {exc}")

    if args.auto_merge:
        set_merge_request_to_auto_merge(client, project_id)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("Argument description of Git happens")
    parser.add_argument("title", nargs="+", help="Title of issue")
    parser.add_argument("--project_id", type=str, help="Id or URL-encoded path of project")
    parser.add_argument(
        "-m",
        "--milestone",
        action="store_true",
        help="Add this flag, if you want to manually select milestone",
    )
    parser.add_argument("--no_epic", action="store_true", help="Add this flag if you don't want to pick epic")
    parser.add_argument(
        "--no_milestone",
        action="store_true",
        help="Add this flag if you don't want to pick milestone",
    )
    parser.add_argument(
        "--no_iteration",
        action="store_true",
        help="Add this flag if you don't want to pick iteration",
    )
    parser.add_argument(
        "--only_issue",
        action="store_true",
        help="Add this flag if you don't want to create merge request and branch alongside issue",
    )
    parser.add_argument(
        "-am",
        "--auto_merge",
        action="store_true",
        help="Add this flag to review if you want to set merge request to auto merge when pipeline succeeds",
    )
    parser.add_argument(
        "--select",
        action="store_true",
        help="Manually select reviewers for merge request (interactive)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if len(sys.argv if argv is None else argv) <= 1:
        parser.print_help()
        return 1

    args = parser.parse_args(argv)
    title = " ".join(args.title)

    try:
        runtime = load_runtime()
        runtime.main_branch = get_main_branch()
        client = GitLabClient.from_config(runtime.config)
    except (FileNotFoundError, GitLabApiError) as exc:
        print(exc)
        return 1

    try:
        if args.title[0] == "report":
            if len(args.title) != 3:
                print('Invalid report format. Use: gh report "text" minutes')
                return 1

            try:
                minutes = int(args.title[2].strip())
            except ValueError:
                print("Invalid minutes. Please provide a valid number.")
                return 1

            process_report(runtime, client, args.title[1], minutes)
            return 0

        if title == "open":
            project_id = _resolve_project_id(client, args.project_id)
            open_merge_request_in_browser(runtime, client, project_id)
            return 0

        if title == "review":
            project_id = _resolve_project_id(client, args.project_id)
            _run_review(runtime, client, args, project_id)
            return 0

        if title == "summary":
            print_recent_commits(get_two_weeks_commits(runtime.config.developer_email))
            return 0

        if title == "summaryAI":
            generate_smart_summary(runtime, get_two_weeks_commits(runtime.config.developer_email))
            return 0

        if title == "last deploy":
            project_id = _resolve_project_id(client, args.project_id)
            get_last_production_deploy(runtime, client, project_id)
            return 0

        if title == "ai review":
            from ai_code_review import run_review

            run_review()
            return 0

        template_name = select_template(get_template_names(runtime.templates, runtime.config.custom_template))
        selected_settings = get_issue_settings(
            template_name,
            runtime.templates,
            runtime.config.custom_template,
        )
        if not selected_settings:
            print("Custom selection of issue settings is not supported yet")
            return 1

        if args.project_id and selected_settings.get("projectIds"):
            print("NOTE: Overwriting project id from argument...")

        project_id = selected_settings.get("projectIds") or args.project_id or _resolve_project_id(client)

        milestone_id = False
        if not args.no_milestone:
            milestone_id = _select_current_milestone(client, args.milestone)["id"]

        iteration = False
        if not args.no_iteration:
            iteration = _select_iteration(client, manual=True)

        epic = False
        if not args.no_epic:
            epic = _select_epic(client)

        only_issue = selected_settings.get("onlyIssue") or args.only_issue

        if isinstance(project_id, list):
            for current_project_id in project_id:
                start_issue_creation(
                    runtime,
                    client,
                    current_project_id,
                    title,
                    milestone_id,
                    epic,
                    iteration,
                    selected_settings,
                    only_issue,
                )
            return 0

        start_issue_creation(
            runtime,
            client,
            project_id,
            title,
            milestone_id,
            epic,
            iteration,
            selected_settings,
            only_issue,
        )
        return 0
    except GitLabApiError as exc:
        print(exc)
        return 1
    except ValueError as exc:
        print(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
