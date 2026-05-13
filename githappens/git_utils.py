from __future__ import annotations

import datetime
import subprocess


def get_project_link_from_current_dir() -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return None

    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8").strip()


def get_current_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    ).strip()


def get_main_branch() -> str:
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(
        command,
        shell=True,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return output.strip()


def get_two_weeks_commits(developer_email: str | None = None) -> str:
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime("%Y-%m-%d")
    command = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if developer_email:
        command = f"{command} | grep {developer_email}"

    try:
        return subprocess.check_output(
            command,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).strip()
    except subprocess.CalledProcessError:
        return ""
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return ""
