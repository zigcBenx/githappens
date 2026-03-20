import configparser
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

ini = configparser.ConfigParser()
_config_path = os.path.join(ROOT, 'configs/config.ini')
ini.read(_config_path)

BASE_URL = ini.get('DEFAULT', 'base_url')
API_URL = BASE_URL + '/api/v4'
GROUP_ID = ini.get('DEFAULT', 'group_id')
CUSTOM_TEMPLATE = ini.get('DEFAULT', 'custom_template')
GITLAB_TOKEN = ini.get('DEFAULT', 'GITLAB_TOKEN').strip('\"\'')
DELETE_BRANCH = ini.get('DEFAULT', 'delete_branch_after_merge').lower() == 'true'
DEVELOPER_EMAIL = ini.get('DEFAULT', 'developer_email', fallback=None)
SQUASH_COMMITS = ini.get('DEFAULT', 'squash_commits').lower() == 'true'
PRODUCTION_PIPELINE_NAME = ini.get('DEFAULT', 'production_pipeline_name', fallback='deploy')
PRODUCTION_JOB_NAME = ini.get('DEFAULT', 'production_job_name', fallback=None)
PRODUCTION_REF = ini.get('DEFAULT', 'production_ref', fallback=None)
MAIN_BRANCH = 'master'

with open(os.path.join(ROOT, 'configs/templates.json'), 'r') as f:
    _json_config = json.load(f)
TEMPLATES = _json_config['templates']
REVIEWERS = _json_config['reviewers']
PRODUCTION_MAPPINGS = _json_config.get('productionMappings', {})

def set_main_branch(name):
    global MAIN_BRANCH
    MAIN_BRANCH = name
