import configparser
import json
import os


class Config:
    
    def __init__(self):
        self.absolute_config_path = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.absolute_config_path, 'configs/config.ini')
        self.templates_path = os.path.join(self.absolute_config_path, 'configs/templates.json')
        
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)
        
        with open(self.templates_path, 'r') as f:
            json_config = json.load(f)
        
        self.BASE_URL = self.config.get('DEFAULT', 'base_url')
        self.API_URL = self.BASE_URL + '/api/v4'
        self.GROUP_ID = self.config.get('DEFAULT', 'group_id')
        self.CUSTOM_TEMPLATE = self.config.get('DEFAULT', 'custom_template')
        self.GITLAB_TOKEN = self.config.get('DEFAULT', 'GITLAB_TOKEN').strip('"\'')
        self.DELETE_BRANCH = self.config.get('DEFAULT', 'delete_branch_after_merge').lower() == 'true'
        self.DEVELOPER_EMAIL = self.config.get('DEFAULT', 'developer_email', fallback=None)
        self.SQUASH_COMMITS = self.config.get('DEFAULT', 'squash_commits').lower() == 'true'
        self.PRODUCTION_PIPELINE_NAME = self.config.get('DEFAULT', 'production_pipeline_name', fallback='deploy')
        self.PRODUCTION_JOB_NAME = self.config.get('DEFAULT', 'production_job_name', fallback=None)
        self.PRODUCTION_REF = self.config.get('DEFAULT', 'production_ref', fallback=None)
        
        self.TEMPLATES = json_config['templates']
        self.REVIEWERS = json_config['reviewers']
        self.PRODUCTION_MAPPINGS = json_config.get('productionMappings', {})
    
    def get(self, section, option, fallback=None):
        return self.config.get(section, option, fallback=fallback)
    
    def get_issue_settings(self, template_name):
        if template_name == self.CUSTOM_TEMPLATE:
            return {}
        return next((t for t in self.TEMPLATES if t['name'] == template_name), None)


# global config instance
_config_instance = None


def get_config():
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
