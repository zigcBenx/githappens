"""Configuration management for gitHappens."""
import configparser
import json
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CONFIG_PATH = os.path.join(_BASE_DIR, 'configs/config.ini')
_TEMPLATES_PATH = os.path.join(_BASE_DIR, 'configs/templates.json')

config = configparser.ConfigParser()
config.read(_CONFIG_PATH)

BASE_URL = config.get('DEFAULT', 'base_url')
API_URL = BASE_URL + '/api/v4'
GROUP_ID = config.get('DEFAULT', 'group_id')
CUSTOM_TEMPLATE = config.get('DEFAULT', 'custom_template')
GITLAB_TOKEN = config.get('DEFAULT', 'GITLAB_TOKEN').strip('\"\'')
DELETE_BRANCH = config.get('DEFAULT', 'delete_branch_after_merge').lower() == 'true'
DEVELOPER_EMAIL = config.get('DEFAULT', 'developer_email', fallback=None)
SQUASH_COMMITS = config.get('DEFAULT', 'squash_commits').lower() == 'true'
PRODUCTION_PIPELINE_NAME = config.get('DEFAULT', 'production_pipeline_name', fallback='deploy')
PRODUCTION_JOB_NAME = config.get('DEFAULT', 'production_job_name', fallback=None)
PRODUCTION_REF = config.get('DEFAULT', 'production_ref', fallback=None)
MAIN_BRANCH = 'master'

with open(_TEMPLATES_PATH, 'r') as f:
    _json_config = json.load(f)

TEMPLATES = _json_config['templates']
REVIEWERS = _json_config['reviewers']
PRODUCTION_MAPPINGS = _json_config.get('productionMappings', {})


def get_incident_project_id():
    """Return the configured incident project ID or None."""
    try:
        return config.get('DEFAULT', 'incident_project_id')
    except (configparser.NoOptionError, configparser.NoSectionError):
        return None


def get_openai_api_key():
    return config.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)


def set_main_branch(name):
    """Update MAIN_BRANCH at runtime (used by main entry point)."""
    global MAIN_BRANCH
    MAIN_BRANCH = name
