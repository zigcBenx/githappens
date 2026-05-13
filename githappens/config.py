import configparser
import os


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT_DIR, "configs")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.ini")
TEMPLATES_PATH = os.path.join(CONFIG_DIR, "templates.json")
MAIN_BRANCH = "master"


def load_config(path=CONFIG_PATH):
    parser = configparser.ConfigParser()
    parser.read(path)
    return parser


config = load_config()


def get_config_value(name, fallback=""):
    return config.get("DEFAULT", name, fallback=fallback)


def get_bool_config(name, fallback=False):
    value = get_config_value(name, str(fallback))
    return str(value).lower() == "true"


BASE_URL = get_config_value("base_url", "https://gitlab.com")
API_URL = BASE_URL + "/api/v4"
GROUP_ID = get_config_value("group_id")
CUSTOM_TEMPLATE = get_config_value("custom_template", "Custom")
GITLAB_TOKEN = get_config_value("GITLAB_TOKEN").strip("\"'")
DELETE_BRANCH = get_bool_config("delete_branch_after_merge", True)
DEVELOPER_EMAIL = get_config_value("developer_email", None)
SQUASH_COMMITS = get_bool_config("squash_commits", True)
PRODUCTION_PIPELINE_NAME = get_config_value("production_pipeline_name", "deploy")
PRODUCTION_JOB_NAME = get_config_value("production_job_name", None)
PRODUCTION_REF = get_config_value("production_ref", None)
