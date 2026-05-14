import os
import configparser

config = configparser.ConfigParser()
absolute_config_path = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(absolute_config_path, 'configs', 'config.ini')
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
