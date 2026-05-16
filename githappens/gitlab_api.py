import datetime
import json
import re
import subprocess

from .config import get_production_mappings, get_reviewers, get_settings
from .git_utils import get_project_link_from_current_dir
from .interactive import prompt_checkbox, prompt_list, prompt_text


MAIN_BRANCH = "master"


def set_main_branch(branch_name):
    global MAIN_BRANCH
    MAIN_BRANCH = branch_name


def _headers():
    return {"PRIVATE-TOKEN": get_settings().gitlab_token}


def _request_headers():
    return {"Private-Token": get_settings().gitlab_token}


def _requests():
    import requests

    return requests


def get_project_id():
    project_link = get_project_link_from_current_dir()
    if project_link == -1:
        return enter_project_id()

    all_projects = get_all_projects(project_link)
    for project in all_projects or []:
        if project.get("ssh_url_to_repo") == project_link:
            return project.get("id")
    return None


def get_all_projects(project_link):
    settings = get_settings()
    url = settings.api_url + "/projects?membership=true&search=" + project_link.split("/")[-1].split(".")[0]
    response = _requests().get(url, headers=_headers())
    if response.status_code == 200:
        return response.json()
    if response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        raise SystemExit(1)
    print(f"Request failed with status code {response.status_code}")
    return None


def enter_project_id():
    while True:
        project_id = input("Please enter the ID of your GitLab project: ")
        if project_id:
            return project_id
        raise SystemExit("Invalid project ID.")


def _glab_json(args):
    result = subprocess.run(["glab", "api", *args], stdout=subprocess.PIPE)
    return json.loads(result.stdout)


def list_milestones(current=False):
    settings = get_settings()
    milestones = _glab_json([f"/groups/{settings.group_id}/milestones?state=active"])
    if current:
        today = datetime.date.today().strftime("%Y-%m-%d")
        active_milestones = [
            milestone for milestone in milestones
            if milestone["start_date"] and milestone["due_date"]
            and milestone["start_date"] <= today <= milestone["due_date"]
        ]
        active_milestones.sort(key=lambda milestone: milestone["due_date"])
        return active_milestones[0]
    return milestones


def select_milestone(milestones):
    answer = prompt_list(
        "milestones",
        message="Select milestone:",
        choices=[milestone["title"] for milestone in milestones],
    )
    return answer["milestones"]


def get_selected_milestone(milestone, milestones):
    return next((item for item in milestones if item["title"] == milestone), None)


def get_milestone(manual):
    if manual:
        milestones = list_milestones()
        return get_selected_milestone(select_milestone(milestones), milestones)
    return list_milestones(True)


def list_iterations():
    settings = get_settings()
    return _glab_json([f"/groups/{settings.group_id}/iterations?state=opened"])


def get_active_iteration():
    iterations = list_iterations()
    today = datetime.date.today().strftime("%Y-%m-%d")
    active_iterations = [
        iteration for iteration in iterations
        if iteration["start_date"] and iteration["due_date"]
        and iteration["start_date"] <= today <= iteration["due_date"]
    ]
    active_iterations.sort(key=lambda iteration: iteration["due_date"])
    return active_iterations[0]


def select_iteration(iterations):
    choices = [item["start_date"] + " - " + item["due_date"] for item in iterations]
    answer = prompt_list("iterations", message="Select iteration:", choices=choices)
    return answer["iterations"]


def get_selected_iteration(iteration, iterations):
    return next((item for item in iterations if item["start_date"] + " - " + item["due_date"] == iteration), None)


def get_iteration(manual):
    if manual:
        iterations = list_iterations()
        return get_selected_iteration(select_iteration(iterations), iterations)
    return get_active_iteration()


def list_epics():
    settings = get_settings()
    return _glab_json([f"/groups/{settings.group_id}/epics?per_page=1000&state=opened"])


def select_epic(epics):
    epic_titles = [epic["title"] for epic in epics]
    search_query = prompt_text("search_query", message="Search epic:")["search_query"]
    filtered_epics = [choice for choice in epic_titles if search_query.lower() in choice.lower()]
    answer = prompt_list("epics", message="Select epic:", choices=filtered_epics)
    return answer["epics"]


def get_selected_epic(epic, epics):
    return next((item for item in epics if item["title"] == epic), None)


def get_epic():
    epics = list_epics()
    return get_selected_epic(select_epic(epics), epics)


def get_authorized_user():
    output = subprocess.check_output(["glab", "api", "/user"])
    return json.loads(output)


def create_issue(title, project_id, milestone_id, epic, iteration, settings):
    if settings:
        issue_type = settings.get("type") or "issue"
        return execute_issue_create(
            project_id,
            title,
            settings.get("labels"),
            milestone_id,
            epic,
            iteration,
            settings.get("weight"),
            settings.get("estimated_time"),
            issue_type,
        )
    print("No settings in template")
    raise SystemExit(2)


def execute_issue_create(project_id, title, labels, milestone_id, epic, iteration, weight, estimated_time, issue_type="issue"):
    labels = ",".join(labels) if isinstance(labels, list) else labels
    assignee_id = get_authorized_user()["id"]
    issue_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/issues",
        "-f", f"title={title}",
        "-f", f"assignee_ids={assignee_id}",
        "-f", f"issue_type={issue_type}",
    ]
    if labels:
        issue_command.extend(["-f", f"labels={labels}"])
    if weight:
        issue_command.extend(["-f", f"weight={str(weight)}"])
    if milestone_id:
        issue_command.extend(["-f", f"milestone_id={str(milestone_id)}"])
    if epic:
        issue_command.extend(["-f", f"epic_id={str(epic['id'])}"])

    description = ""
    if iteration:
        description += f"/iteration *iteration:{str(iteration['id'])} "
    if estimated_time:
        description += f"\n/estimate {estimated_time}m "
    issue_command.extend(["-f", f"description={description}"])

    issue_output = subprocess.check_output(issue_command)
    return json.loads(issue_output.decode())


def create_branch(project_id, issue):
    issue_id = str(issue["iid"])
    title = re.sub("\\s+", "-", issue["title"]).lower()
    title = issue_id + "-" + title.replace(":", "").replace("(", " ").replace(")", "").replace(" ", "-")
    branch_output = subprocess.check_output([
        "glab", "api",
        f"/projects/{str(project_id)}/repository/branches",
        "-f", f"branch={title}",
        "-f", f"ref={MAIN_BRANCH}",
        "-f", f"issue_iid={issue_id}",
    ])
    return json.loads(branch_output.decode())


def create_merge_request(project_id, branch, issue, labels, milestone_id):
    settings = get_settings()
    issue_id = str(issue["iid"])
    branch_name = branch["name"]
    assignee_id = get_authorized_user()["id"]
    labels = ",".join(labels) if isinstance(labels, list) else labels
    merge_request_command = [
        "glab", "api",
        f"/projects/{str(project_id)}/merge_requests",
        "-f", f"title={issue['title']}",
        "-f", f"description=\"Closes #{issue_id}\"",
        "-f", f"source_branch={branch_name}",
        "-f", f"target_branch={MAIN_BRANCH}",
        "-f", f"issue_iid={issue_id}",
        "-f", f"assignee_ids={assignee_id}",
    ]
    if settings.squash_commits:
        merge_request_command.extend(["-f", "squash=true"])
    if settings.delete_branch:
        merge_request_command.extend(["-f", "remove_source_branch=true"])
    if labels:
        merge_request_command.extend(["-f", f"labels={labels}"])
    if milestone_id:
        merge_request_command.extend(["-f", f"milestone_id={str(milestone_id)}"])

    mr_output = subprocess.check_output(merge_request_command)
    return json.loads(mr_output.decode())


def get_merge_request_for_branch(branch_name):
    settings = get_settings()
    project_id = get_project_id()
    api_url = f"{settings.api_url}/projects/{project_id}/merge_requests"
    response = _requests().get(api_url, headers=_request_headers(), params={"source_branch": branch_name})
    if response.status_code == 200:
        for mr in response.json():
            if mr["source_branch"] == branch_name:
                return mr
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None


def find_merge_request_id_by_branch(branch_name):
    return get_merge_request_for_branch(branch_name)["iid"]


def get_labels_of_group(search=""):
    settings = get_settings()
    try:
        return _glab_json([f"/groups/{settings.group_id}/labels?search={search}"])
    except subprocess.CalledProcessError as error:
        print(f"Error getting labels: {str(error)}")
        return []


def select_labels(search, multiple=False):
    labels = sorted([label["name"] for label in get_labels_of_group(search)])
    prompt = prompt_checkbox if multiple else prompt_list
    answer = prompt("labels", message="Select one or more department labels:", choices=labels)
    return answer["labels"]


def get_reviewers_with_names():
    reviewer_choices = []
    settings = get_settings()
    for reviewer_id in get_reviewers():
        api_url = f"{settings.api_url}/users/{reviewer_id}"
        try:
            response = _requests().get(api_url, headers=_request_headers())
            if response.status_code == 200:
                user = response.json()
                reviewer_choices.append((f"{user.get('name')} ({user.get('username')})", reviewer_id))
            else:
                reviewer_choices.append((str(reviewer_id), reviewer_id))
        except Exception:
            reviewer_choices.append((str(reviewer_id), reviewer_id))
    return reviewer_choices


def put_merge_request_reviewers(project_id, mr_id, reviewers=None):
    settings = get_settings()
    api_url = f"{settings.api_url}/projects/{project_id}/merge_requests/{mr_id}"
    _requests().put(api_url, headers=_request_headers(), json={"reviewer_ids": reviewers if reviewers is not None else get_reviewers()})


def put_merge_request_auto_merge(project_id, mr_id):
    settings = get_settings()
    api_url = f"{settings.api_url}/projects/{project_id}/merge_requests/{mr_id}/merge"
    _requests().put(
        api_url,
        headers=_request_headers(),
        json={
            "id": project_id,
            "merge_request_iid": mr_id,
            "should_remove_source_branch": True,
            "merge_when_pipeline_succeeds": True,
            "auto_merge_strategy": "merge_when_pipeline_succeeds",
        },
    )


def close_opened_issue(issue_iid, project_id):
    issue_command = [
        "glab", "api",
        f"/projects/{project_id}/issues/{issue_iid}",
        "-X", "PUT",
        "-f", "state_event=close",
    ]
    try:
        subprocess.run(issue_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        print(f"Error closing issue: {str(error)}")


def fetch_project_pipelines(project_id, params):
    settings = get_settings()
    response = _requests().get(f"{settings.api_url}/projects/{project_id}/pipelines", headers=_request_headers(), params=params)
    return response


def fetch_pipeline_jobs(project_id, pipeline_id):
    settings = get_settings()
    return _requests().get(f"{settings.api_url}/projects/{project_id}/pipelines/{pipeline_id}/jobs", headers=_request_headers())


def production_mappings():
    return get_production_mappings()
