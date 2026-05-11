from __future__ import annotations

import datetime
import subprocess


def get_project_link_from_current_dir() -> str | None:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    return result.stdout.strip()


def enter_project_id() -> str:
    while True:
        project_id = input("Please enter the ID of your GitLab project: ").strip()
        if project_id:
            return project_id
        raise SystemExit("Invalid project ID.")


def get_current_branch() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        text=True,
    ).strip()


def get_main_branch(fallback: str = "master") -> str:
    try:
        output = subprocess.check_output(
            "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'",
            shell=True,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except subprocess.CalledProcessError:
        return fallback

    branch = output.strip()
    return branch or fallback


def build_branch_name(issue_iid: int | str, title: str) -> str:
    branch_title = "-".join(title.lower().split())
    branch_title = branch_title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    return f"{issue_iid}-{branch_title}"


def get_project_search_term(remote_url: str) -> str:
    tail = remote_url.rstrip("/").split("/")[-1]
    return tail.removesuffix(".git")


def _extract_repo_path(remote_url: str) -> str:
    cleaned = remote_url.strip()
    if cleaned.startswith("git@"):
        return cleaned.split(":", 1)[1].removesuffix(".git").lower()
    if "://" in cleaned:
        return cleaned.split("://", 1)[1].split("/", 1)[1].removesuffix(".git").lower()
    return cleaned.removesuffix(".git").lower()


def find_matching_project_id(projects: list[dict], remote_url: str) -> int | str | None:
    target_path = _extract_repo_path(remote_url)

    for project in projects:
        candidates = [
            project.get("ssh_url_to_repo"),
            project.get("http_url_to_repo"),
            project.get("path_with_namespace"),
        ]
        for candidate in candidates:
            if candidate and _extract_repo_path(candidate) == target_path:
                return project.get("id")

    return None


def build_merge_request_url(base_url: str, remote_url: str, merge_request_id: int | str) -> str:
    repo_path = _extract_repo_path(remote_url)
    return f"{base_url.rstrip('/')}/{repo_path}/-/merge_requests/{merge_request_id}"


def get_two_weeks_commits(developer_email: str | None = None) -> str:
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime("%Y-%m-%d")
    command = [
        "git",
        "log",
        f"--since={two_weeks_ago}",
        "--format=%ad - %ae - %s",
        "--date=short",
    ]

    try:
        output = subprocess.check_output(
            command,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        print(f"No commits were found or an error occurred. (exit status {exc.returncode})")
        return ""
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return ""

    lines = [line for line in output.splitlines() if "Merge branch" not in line]

    if developer_email:
        lines = [line for line in lines if developer_email in line]

    return "\n".join(lines).strip()
