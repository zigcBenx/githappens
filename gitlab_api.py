import requests
from config import API_URL, GITLAB_TOKEN

def get_all_projects(project_link):
    url = API_URL + "/projects?membership=true&search=" + project_link.split('/')[-1].split('.')[0]
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        print("Error: Unauthorized (401). Your GitLab token is probably expired, invalid, or missing required permissions.")
        print("Please generate a new token and update your configs/config.ini.")
        import sys
        sys.exit(1)
    else:
        print(f"Request failed with status code {response.status_code}")
        return None

def get_merge_request_for_branch(project_id, branch_name):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests"
    headers = {"Private-Token": GITLAB_TOKEN}
    params = {"source_branch": branch_name}
    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        merge_requests = response.json()
        for mr in merge_requests:
            if mr["source_branch"] == branch_name:
                return mr
    else:
        print(f"Failed to fetch Merge Requests: {response.status_code} - {response.text}")
    return None

def get_user_details(user_id):
    api_url = f"{API_URL}/users/{user_id}"
    headers = {"Private-Token": GITLAB_TOKEN}
    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

def update_merge_request_reviewers(project_id, mr_id, reviewers):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": GITLAB_TOKEN}
    data = {"reviewer_ids": reviewers}
    requests.put(api_url, headers=headers, json=data)

def set_mr_auto_merge(project_id, mr_id):
    api_url = f"{API_URL}/projects/{project_id}/merge_requests/{mr_id}/merge"
    headers = {"Private-Token": GITLAB_TOKEN}
    data = {
        "id": project_id,
        "merge_request_iid": mr_id,
        "should_remove_source_branch": True,
        "merge_when_pipeline_succeeds": True,
        "auto_merge_strategy": "merge_when_pipeline_succeeds",
    }
    requests.put(api_url, headers=headers, json=data)

def get_pipelines(project_id, ref=None):
    api_url = f"{API_URL}/projects/{project_id}/pipelines"
    headers = {"Private-Token": GITLAB_TOKEN}
    params = {
        "per_page": 50,
        "order_by": "updated_at",
        "sort": "desc"
    }
    if ref:
        params["ref"] = ref
    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch pipelines: {response.status_code} - {response.text}")
        return None

def get_pipeline_jobs(project_id, pipeline_id):
    url = f"{API_URL}/projects/{project_id}/pipelines/{pipeline_id}/jobs"
    headers = {"Private-Token": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return None
