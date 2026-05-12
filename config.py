#!/usr/bin/env python3
import configparser
import json
import os

config = configparser.ConfigParser()
_absolute_config_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(_absolute_config_path, 'configs', 'config.ini')
config.read(config_path)

BASE_URL = config.get('DEFAULT', 'base_url')
API_URL = BASE_URL + '/api/v4'
GROUP_ID = config.get('DEFAULT', 'group_id')
CUSTOM_TEMPLATE = config.get('DEFAULT', 'custom_template')
GITLAB_TOKEN = config.get('DEFAULT', 'GITLAB_TOKEN').strip('"\'')
DELETE_BRANCH = config.get('DEFAULT', 'delete_branch_after_merge').lower() == 'true'
DEVELOPER_EMAIL = config.get('DEFAULT', 'developer_email', fallback=None)
SQUASH_COMMITS = config.get('DEFAULT', 'squash_commits').lower() == 'true'
PRODUCTION_PIPELINE_NAME = config.get('DEFAULT', 'production_pipeline_name', fallback='deploy')
PRODUCTION_JOB_NAME = config.get('DEFAULT', 'production_job_name', fallback=None)
PRODUCTION_REF = config.get('DEFAULT', 'production_ref', fallback=None)
MAIN_BRANCH = 'master'

# Read templates from json config
_templates_json_path = os.path.join(_absolute_config_path, 'configs', 'templates.json')
if os.path.exists(_templates_json_path):
    with open(_templates_json_path, 'r') as f:
        _json_config = json.load(f)
    TEMPLATES = _json_config.get('templates', [])
    REVIEWERS = _json_config.get('reviewers', [])
    PRODUCTION_MAPPINGS = _json_config.get('productionMappings', {})
else:
    TEMPLATES = []
    REVIEWERS = []
    PRODUCTION_MAPPINGS = {}
