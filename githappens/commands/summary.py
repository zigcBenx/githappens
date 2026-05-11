"""Summary command helpers."""

from __future__ import annotations

from githappens.git_utils import get_two_weeks_commits


def print_two_weeks_commits(developer_email: str | None = None) -> None:
    commits = get_two_weeks_commits(developer_email)
    if commits:
        print(commits)
    else:
        print("No commits found.")
