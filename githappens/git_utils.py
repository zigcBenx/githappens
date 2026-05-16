import subprocess


def get_project_link_from_current_dir():
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError:
        return -1
    if result.returncode == 0:
        return result.stdout.decode("utf-8").strip()
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
