"""Configuration management for GitHappens CLI.

All config values are accessed through getters here. Config is lazy-loaded
on first access, so this module can be imported without side effects.
"""
import os
import subprocess
import configparser

_config = None
_abs_config_path = None


def _load_config():
    global _config, _abs_config_path
    if _config is None:
        _config = configparser.ConfigParser()
        _abs_config_path = os.path.dirname(os.path.abspath(__file__))
        _config.read(os.path.join(_abs_config_path, 'configs', 'config.ini'))
    return _config


def _abs_path():
    global _abs_config_path
    if _abs_config_path is None:
        _load_config()
    return _abs_config_path


# ── Config value getters ────────────────────────────────────────────────────

def get_base_url():
    return _load_config().get('DEFAULT', 'base_url')


def get_api_url():
    return get_base_url() + '/api/v4'


def get_group_id():
    return _load_config().get('DEFAULT', 'group_id')


def get_custom_template():
    return _load_config().get('DEFAULT', 'custom_template')


def get_gitlab_token():
    return _load_config().get('DEFAULT', 'GITLAB_TOKEN').strip('"\'')


def get_delete_branch_after_merge():
    return _load_config().get('DEFAULT', 'delete_branch_after_merge').lower() == 'true'


def get_developer_email():
    return _load_config().get('DEFAULT', 'developer_email', fallback=None)


def get_squash_commits():
    return _load_config().get('DEFAULT', 'squash_commits').lower() == 'true'


def get_production_pipeline_name():
    return _load_config().get('DEFAULT', 'production_pipeline_name', fallback='deploy')


def get_production_job_name():
    return _load_config().get('DEFAULT', 'production_job_name', fallback=None)


def get_production_ref():
    return _load_config().get('DEFAULT', 'production_ref', fallback=None)


def get_openai_api_key():
    return _load_config().get('DEFAULT', 'OPENAI_API_KEY', fallback=None)


def get_incident_project_id():
    return _load_config().get('DEFAULT', 'incident_project_id')


def get_main_branch():
    """Detect the default main branch name from git remote HEAD."""
    cmd = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
    return output.strip()


def get_project_link_from_current_dir():
    """Return git remote URL for current repo, or -1 on failure."""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            return result.stdout.decode('utf-8').strip()
        return -1
    except FileNotFoundError:
        return -1


def enter_project_id():
    """Prompt user to manually enter a GitLab project ID."""
    while True:
        project_id = input('Please enter the ID of your GitLab project: ')
        if project_id:
            return project_id
        exit('Invalid project ID.')


def get_project_id():
    """Resolve the GitLab project ID from the current git remote or user input."""
    project_link = get_project_link_from_current_dir()
    if project_link == -1:
        return enter_project_id()
    from gitlab_api import get_all_projects
    all_projects = get_all_projects(project_link)
    for project in all_projects:
        if project.get("ssh_url_to_repo") == project_link:
            return project.get("id")
    return None


def get_templates_data():
    """Load templates, reviewers, and production mappings from templates.json."""
    import json
    with open(os.path.join(_abs_path(), 'configs', 'templates.json'), 'r') as f:
        data = json.load(f)
    return data.get('templates', []), data.get('reviewers', []), data.get('productionMappings', {})