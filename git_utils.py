#!/usr/bin/env python3
import subprocess
import datetime
import webbrowser

import config


class Colors:
    CRITICAL = '\033[91m'
    HIGH = '\033[93m'
    INFO = '\033[96m'
    RESET = '\033[0m'


def get_project_link_from_current_dir():
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return result.stdout.decode('utf-8').strip()
        return -1
    except FileNotFoundError:
        return -1


def get_current_branch():
    return subprocess.check_output(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
        text=True,
    ).strip()


def get_main_branch():
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(
        command,
        shell=True,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return output.strip()


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime('%Y-%m-%d')
    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if config.DEVELOPER_EMAIL:
        cmd = f'{cmd} | grep {config.DEVELOPER_EMAIL}'
    try:
        output = subprocess.check_output(
            cmd,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).strip()
        if output:
            if return_output:
                return output
            print(output)
        else:
            print("No commits found.")
            return "" if return_output else None
    except subprocess.CalledProcessError as e:
        print(f"No commits were found or an error occurred. (exit status {e.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None


def open_merge_request_in_browser():
    import gitlab_api
    try:
        merge_request_id = gitlab_api.get_active_merge_request_id()
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True,
        ).strip()
        url = config.BASE_URL + '/' + remote_url.split(':')[1][:-4]
        webbrowser.open(f"{url}/-/merge_requests/{merge_request_id}")
    except subprocess.CalledProcessError:
        return None


def get_branch_diff():
    """Get the diff of changed files in current branch vs main branch."""
    try:
        main_branch = subprocess.check_output(
            "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'",
            shell=True, text=True, stderr=subprocess.STDOUT
        ).strip()
    except subprocess.CalledProcessError:
        main_branch = 'master'

    try:
        current_branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            text=True,
        ).strip()

        if current_branch == main_branch:
            print(f"{Colors.HIGH}⚠ You are on the main branch ({main_branch}). No changes to review.{Colors.RESET}")
            return None

        diff_output = subprocess.check_output(
            ['git', 'diff', f'{main_branch}...HEAD'],
            text=True,
            stderr=subprocess.DEVNULL,
        )

        if not diff_output.strip():
            print(f"{Colors.INFO}ℹ No changes detected between {current_branch} and {main_branch}{Colors.RESET}")
            return None

        return diff_output
    except subprocess.CalledProcessError as e:
        print(f"{Colors.CRITICAL}✗ Error getting git diff: {e}{Colors.RESET}")
        return None
