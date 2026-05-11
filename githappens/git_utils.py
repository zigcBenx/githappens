import datetime
import re
import subprocess

from .config import get_settings


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


def issue_branch_name(issue: dict) -> str:
    issue_id = str(issue["iid"])
    title = re.sub(r"\s+", "-", issue["title"]).lower()
    title = title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    return f"{issue_id}-{title}"


def get_current_branch() -> str:
    return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()


def get_main_branch() -> str:
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    return output.strip()


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime("%Y-%m-%d")
    settings = get_settings()

    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if settings.developer_email:
        cmd = f"{cmd} | grep {settings.developer_email}"

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


getProjectLinkFromCurrentDir = get_project_link_from_current_dir
getCurrentBranch = get_current_branch
getMainBranch = get_main_branch

