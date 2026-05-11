import datetime
import subprocess

import config


def get_project_link_from_current_dir():
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return -1
    except FileNotFoundError:
        return -1


def get_current_branch():
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    ).strip()


def get_main_branch():
    output = subprocess.check_output(
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        stderr=subprocess.STDOUT,
        text=True,
    )
    return output.strip().split("/", 1)[-1]


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime("%Y-%m-%d")
    command = [
        "git",
        "log",
        f"--since={two_weeks_ago}",
        "--format=%ad - %ae - %s",
        "--date=short",
    ]

    try:
        output = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError as error:
        print(f"No commits were found or an error occurred. (exit status {error.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None

    lines = [line for line in output.splitlines() if "Merge branch" not in line]
    if config.DEVELOPER_EMAIL:
        lines = [line for line in lines if config.DEVELOPER_EMAIL in line]

    result = "\n".join(lines).strip()
    if result:
        if return_output:
            return result
        print(result)
        return None

    print("No commits found.")
    return "" if return_output else None
