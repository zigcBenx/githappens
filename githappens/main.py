import argparse
import sys

from . import git_utils, interactive, templates
from .commands.create_issue import create_issue_flow
from .commands.deploy import get_last_production_deploy
from .commands.open_mr import open_merge_request_in_browser
from .commands.report import process_report
from .commands.review import review_flow


def generate_smart_summary():
    from . import config

    commits = git_utils.get_two_weeks_commits(return_output=True)
    if not commits:
        return

    openai_api_key = config.config.get("DEFAULT", "OPENAI_API_KEY", fallback=None)
    if not openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Please install it using: pip install openai")
        return

    openai.api_key = openai_api_key

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes git commits. Provide a concise, well-organized summary of the main changes and themes.",
                },
                {
                    "role": "user",
                    "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}",
                },
            ],
        )

        print("\n📋 AI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as error:
        print(f"Error generating AI summary: {error}")


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
            process_report(text, int(parts[2].strip()))
        except ValueError:
            print("Invalid minutes. Please provide a valid number.")
        return

    title = " ".join(args.title)

    if title == "open":
        open_merge_request_in_browser()
        return
    if title == "review":
        review_flow(auto_merge=args.auto_merge, select=getattr(args, "select", False))
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

    selected_settings = templates.get_issue_settings(interactive.select_template())

    if not len(selected_settings):
        print("Custom selection of issue settings is not supported yet")

    create_issue_flow(title, args, selected_settings)


if __name__ == "__main__":
    main()
