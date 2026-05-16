import argparse
import sys


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
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    if not argv:
        parser.print_help()
        raise SystemExit(1)

    args = parser.parse_args(argv)
    if args.title[0] == "report":
        from .commands.report import process_report

        if len(args.title) != 3:
            print('Invalid report format. Use: gh report "text" minutes')
            return
        try:
            process_report(args.title[1], int(args.title[2].strip()))
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    title = " ".join(args.title)
    if title == "open":
        from .commands.open_mr import open_merge_request_in_browser

        open_merge_request_in_browser()
        return
    if title == "review":
        from .commands.review import review_command

        review_command(select=args.select, auto_merge=args.auto_merge)
        return
    if title == "summary":
        from .commands.summary import get_two_weeks_commits

        get_two_weeks_commits()
        return
    if title == "summaryAI":
        from .commands.summary import generate_smart_summary

        generate_smart_summary()
        return
    if title == "last deploy":
        from .commands.deploy import get_last_production_deploy

        get_last_production_deploy()
        return
    if title == "ai review":
        from ai_code_review import run_review

        run_review()
        return

    from .commands.create_issue import start_issue_creation
    from .git_utils import get_main_branch
    from .gitlab_api import get_epic, get_iteration, get_milestone, get_project_id, set_main_branch
    from .interactive import prompt_list
    from .templates import get_issue_settings, select_template

    selected_settings = get_issue_settings(select_template(prompt_list))
    if not len(selected_settings):
        print("Custom selection of issue settings is not supported yet")

    if args.project_id and selected_settings.get("projectIds"):
        print("NOTE: Overwriting project id from argument...")

    project_id = selected_settings.get("projectIds") or args.project_id or get_project_id()

    milestone = False
    if not args.no_milestone:
        milestone = get_milestone(args.milestone)["id"]

    iteration = False
    if not args.no_iteration:
        iteration = get_iteration(True)

    epic = False
    if not args.no_epic:
        epic = get_epic()

    set_main_branch(get_main_branch())
    only_issue = selected_settings.get("onlyIssue") or args.only_issue

    if isinstance(project_id, list):
        for item in project_id:
            start_issue_creation(item, title, milestone, epic, iteration, selected_settings, only_issue)
    else:
        start_issue_creation(project_id, title, milestone, epic, iteration, selected_settings, only_issue)
