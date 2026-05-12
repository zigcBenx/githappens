import datetime
import re
import subprocess


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


def get_current_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()


def get_main_branch() -> str:
    output = subprocess.check_output(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        stderr=subprocess.STDOUT,
        text=True,
    )
    return output.strip().replace("refs/remotes/origin/", "")


def build_branch_name(issue: dict) -> str:
    issue_id = str(issue["iid"])
    title = re.sub(r"\s+", "-", issue["title"]).lower()
    title = title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    return f"{issue_id}-{title}"


def get_two_weeks_commits(ctx, return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime(
        "%Y-%m-%d"
    )
    command = [
        "git",
        "log",
        f"--since={two_weeks_ago}",
        '--format=%ad - %ae - %s',
        "--date=short",
    ]

    try:
        output = subprocess.check_output(
            command,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError as exc:
        print(f"No commits were found or an error occurred. (exit status {exc.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None

    commits = []
    for line in output.splitlines():
        if "Merge branch" in line:
            continue
        if ctx.settings.developer_email and ctx.settings.developer_email not in line:
            continue
        commits.append(line)

    if commits:
        result = "\n".join(commits)
        if return_output:
            return result
        print(result)
        return None

    print("No commits found.")
    return "" if return_output else None
