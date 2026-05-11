import configparser
import os


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(ROOT_DIR, "configs")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.ini")
TEMPLATES_PATH = os.path.join(CONFIG_DIR, "templates.json")

CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)


def _get(name, fallback=None):
    return CONFIG.get("DEFAULT", name, fallback=fallback)


def _get_bool(name, fallback=False):
    value = _get(name, str(fallback))
    return str(value).lower() == "true"


BASE_URL = (_get("base_url", "") or "").rstrip("/")
API_URL = f"{BASE_URL}/api/v4" if BASE_URL else "/api/v4"
GROUP_ID = _get("group_id", "")
CUSTOM_TEMPLATE = _get("custom_template", "Custom")
GITLAB_TOKEN = (_get("GITLAB_TOKEN", "") or "").strip("\"'")
DELETE_BRANCH = _get_bool("delete_branch_after_merge", False)
DEVELOPER_EMAIL = _get("developer_email", fallback=None)
SQUASH_COMMITS = _get_bool("squash_commits", False)
PRODUCTION_PIPELINE_NAME = _get("production_pipeline_name", fallback="deploy")
PRODUCTION_JOB_NAME = _get("production_job_name", fallback=None)
PRODUCTION_REF = _get("production_ref", fallback=None)
MAIN_BRANCH = "master"
