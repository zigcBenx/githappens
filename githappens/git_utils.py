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
    output = subprocess.check_output(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        stderr=subprocess.STDOUT,
        text=True,
    )
    return output.strip().removeprefix("refs/remotes/origin/")


def get_two_weeks_commits(developer_email: str | None = None) -> str:
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime("%Y-%m-%d")
    command = ["git", "log", f"--since={two_weeks_ago}", "--format=%ad - %ae - %s", "--date=short"]
    if developer_email:
        command.append(f"--author={developer_email}")

    try:
        output = subprocess.check_output(
            command,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        commits = [line for line in output.splitlines() if "Merge branch" not in line]
        return "\n".join(commits).strip()
    except subprocess.CalledProcessError:
        return ""
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return ""
