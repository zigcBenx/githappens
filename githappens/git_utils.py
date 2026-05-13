import datetime
import subprocess

from . import config


def get_project_link_from_current_dir():
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8").strip()
        return -1
    except FileNotFoundError:
        return -1


def get_current_branch():
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()


def get_main_branch():
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(
        command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True
    )
    return output.strip()


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (
        datetime.datetime.now() - datetime.timedelta(weeks=2)
    ).strftime("%Y-%m-%d")

    try:
        output = subprocess.check_output(
            [
                "git",
                "log",
                f"--since={two_weeks_ago}",
                "--format=%ad - %ae - %s",
                "--date=short",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        )
        lines = [
            line
            for line in output.splitlines()
            if "Merge branch" not in line
            and (not config.DEVELOPER_EMAIL or config.DEVELOPER_EMAIL in line)
        ]
        output = "\n".join(lines).strip()
        if output:
            if return_output:
                return output
            print(output)
        else:
            print("No commits found.")
            return "" if return_output else None
    except subprocess.CalledProcessError as error:
        print(f"No commits were found or an error occurred. (exit status {error.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None
