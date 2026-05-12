import datetime
import subprocess

from config import DEVELOPER_EMAIL


def getProjectLinkFromCurrentDir():
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


def getCurrentBranch():
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()


def getMainBranch():
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(
        command,
        shell=True,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    return output.strip()


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (
        datetime.datetime.now() - datetime.timedelta(weeks=2)
    ).strftime("%Y-%m-%d")

    cmd = (
        f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" '
        '--date=short | grep -v "Merge branch"'
    )
    if DEVELOPER_EMAIL:
        cmd = f"{cmd} | grep {DEVELOPER_EMAIL}"
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
    except subprocess.CalledProcessError as error:
        print(f"No commits were found or an error occurred. (exit status {error.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None
