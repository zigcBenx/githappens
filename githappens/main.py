from __future__ import annotations

import argparse
import sys

from . import git_utils, interactive, templates
from .commands import create_issue, deploy, open_mr, report, review, summary
from .config import load_config


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


def main() -> None:
    parser = build_parser()
    if len(sys.argv) <= 1:
        parser.print_help()
        raise SystemExit(1)

    config = load_config()
    args = parser.parse_args()
    title = " ".join(args.title)

    if args.title[0] == "report":
        _run_report(config, args.title)
        return

    if title == "open":
        open_mr.open_merge_request_in_browser(config)
        return
    if title == "review":
        review.run(config, args)
        return
    if title == "summary":
        git_utils.get_two_weeks_commits(config.developer_email)
        return
    if title == "summaryAI":
        summary.generate_smart_summary(config)
        return
    if title == "last deploy":
        deploy.get_last_production_deploy(config)
        return
    if title == "ai review":
        from ai_code_review import run_review

        run_review()
        return

    selected_settings = templates.get_issue_settings(config, interactive.select_template(config))
    if not len(selected_settings):
        print("Custom selection of issue settings is not supported yet")
    create_issue.run(config, args, title, selected_settings)


def _run_report(config, parts: list[str]) -> None:
    if len(parts) != 3:
        print('Invalid report format. Use: gh report "text" minutes')
        return
    try:
        report.process_report(config, parts[1], int(parts[2].strip()))
    except ValueError:
        print("Invalid minutes. Please provide a valid number.")

