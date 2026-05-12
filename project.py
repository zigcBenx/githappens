"""Helpers to resolve the current GitLab project id."""
import git_utils
import gitlab_api
import interactive


def get_project_id():
    project_link = git_utils.get_project_link_from_current_dir()
    if project_link == -1:
        return interactive.enter_project_id()

    all_projects = gitlab_api.get_all_projects(project_link)
    if not all_projects:
        return None
    for project in all_projects:
        if project.get("ssh_url_to_repo") == project_link:
            return project.get("id")
    return None
