"""Git helpers used by GitHappens commands."""

from __future__ import annotations

import datetime as _dt
import subprocess


def get_project_link_from_current_dir() -> str | int:
    """Return the current repository's origin URL, or -1 if unavailable."""
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
    """Return the active git branch name."""
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()


def get_main_branch() -> str:
    """Return the remote default branch for origin."""
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    return subprocess.check_output(
        command,
        shell=True,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    ).strip()


def get_two_weeks_commits(developer_email: str | None = None) -> str:
    """Return non-merge commits from the last two weeks.

    The original command printed directly. Returning a string makes this easy to
    test and lets command handlers decide how to render empty results/errors.
    """
    two_weeks_ago = (_dt.datetime.now() - _dt.timedelta(weeks=2)).strftime("%Y-%m-%d")
    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if developer_email:
        cmd = f"{cmd} | grep {developer_email}"

    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            text=True,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
