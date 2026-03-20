import subprocess

def getProjectLinkFromCurrentDir():
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

def getCurrentBranch():
    return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()

def getMainBranch():
    command = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    return output.strip()
