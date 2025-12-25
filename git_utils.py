import subprocess
import datetime

from config import get_config


def get_project_link_from_current_dir():
    try:
        cmd = 'git remote get-url origin'
        result = subprocess.run(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            output = result.stdout.decode('utf-8').strip()
            return output
        else:
            return -1
    except FileNotFoundError:
        return -1


def get_current_branch():
    return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()


def get_main_branch():
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    return output.strip()


def get_two_weeks_commits(return_output=False):
    config = get_config()
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime('%Y-%m-%d')
    
    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if config.DEVELOPER_EMAIL:
        cmd = f'{cmd} | grep {config.DEVELOPER_EMAIL}'
    try:
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, universal_newlines=True).strip()
        if output:
            if return_output:
                return output
            print(output)
        else:
            print("No commits found.")
            return "" if return_output else None
    except subprocess.CalledProcessError as e:
        print(f"No commits were found or an error occurred. (exit status {e.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None
