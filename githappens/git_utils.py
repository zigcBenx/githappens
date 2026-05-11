from __future__ import annotations

import datetime
import re
import subprocess


def get_project_link_from_current_dir() -> str | int:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return -1

    if result.returncode != 0:
        return -1
    return result.stdout.decode("utf-8").strip()


def get_current_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    ).strip()


def get_main_branch() -> str:
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    return subprocess.check_output(
        command,
        shell=True,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ).strip()


def branch_name_for_issue(issue: dict[str, object]) -> str:
    issue_id = str(issue["iid"])
    title = str(issue["title"])
    title = re.sub(r"\s+", "-", title).lower()
    title = title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    return f"{issue_id}-{title}"


def get_two_weeks_commits(developer_email: str | None = None, return_output: bool = False) -> str | None:
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime("%Y-%m-%d")
    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if developer_email:
        cmd = f"{cmd} | grep {developer_email}"

    try:
        output = subprocess.check_output(
            cmd,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).strip()
    except subprocess.CalledProcessError as error:
        print(f"No commits were found or an error occurred. (exit status {error.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None

    if output:
        if return_output:
            return output
        print(output)
        return None

    print("No commits found.")
    return "" if return_output else None
