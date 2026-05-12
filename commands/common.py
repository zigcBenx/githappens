import subprocess
import json
from config import GROUP_ID
import gitlab_api
import interactive
import git_utils

def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)

def list_milestones(current=False):
    cmd = f'glab api /groups/{GROUP_ID}/milestones?state=active'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    milestones = json.loads(result.stdout)
    if current:
        import datetime
        today = datetime.date.today().strftime('%Y-%m-%d')
        active_milestones = []
        for milestone in milestones:
            start_date = milestone['start_date']
            due_date = milestone['due_date']
            if start_date and due_date and start_date <= today and due_date >= today:
                active_milestones.append(milestone)
        active_milestones.sort(key=lambda x: x['due_date'])
        return active_milestones[0] if active_milestones else None
    return milestones

def list_iterations():
    cmd = f'glab api /groups/{GROUP_ID}/iterations?state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)

def get_active_iteration():
    iterations = list_iterations()
    import datetime
    today = datetime.date.today().strftime('%Y-%m-%d')
    active_iterations = []
    for iteration in iterations:
        start_date = iteration['start_date']
        due_date = iteration['due_date']
        if start_date and due_date and start_date <= today and due_date >= today:
            active_iterations.append(iteration)
    active_iterations.sort(key=lambda x: x['due_date'])
    return active_iterations[0] if active_iterations else None

def list_epics():
    cmd = f'glab api /groups/{GROUP_ID}/epics?per_page=1000&state=opened'
    result = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    return json.loads(result.stdout)

def get_milestone(manual):
    if manual:
        milestones = list_milestones()
        selected_title = interactive.select_milestone(milestones)
        return next((t for t in milestones if t['title'] == selected_title), None)
    return list_milestones(True)

def get_iteration(manual):
    if manual:
        iterations = list_iterations()
        selected_range = interactive.select_iteration(iterations)
        return next((t for t in iterations if t['start_date'] + ' - ' + t['due_date'] == selected_range), None)
    return get_active_iteration()

def get_epic():
    epics = list_epics()
    selected_title = interactive.select_epic(epics)
    return next((t for t in epics if t['title'] == selected_title), None)

def get_project_id():
    link = git_utils.get_project_link_from_current_dir()
    if link == -1:
        # enter_project_id logic
        import inquirer
        while True:
            project_id = inquirer.Text('pid', message='Please enter the ID of your GitLab project:').prompt()
            if project_id: return project_id
            exit('Invalid project ID.')
    
    projects = gitlab_api.get_all_projects(link)
    for project in projects:
        if project.get("ssh_url_to_repo") == link:
            return project.get("id")
    return None
