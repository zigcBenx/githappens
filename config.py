import configparser
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = ROOT_DIR / "configs"
CONFIG_PATH = CONFIG_DIR / "config.ini"
TEMPLATES_PATH = CONFIG_DIR / "templates.json"


def load_config(path=CONFIG_PATH):
    parser = configparser.ConfigParser()
    parser.read(path)
    return parser


CONFIG = load_config()


def config_value(option, fallback="", strip_quotes=False):
    value = CONFIG.get("DEFAULT", option, fallback=fallback)
    if strip_quotes and isinstance(value, str):
        return value.strip("\"'")
    return value


def config_bool(option, fallback=False):
    value = CONFIG.get("DEFAULT", option, fallback=str(fallback))
    return str(value).lower() == "true"


BASE_URL = config_value("base_url", "https://gitlab.com")
API_URL = f"{BASE_URL}/api/v4"
GROUP_ID = config_value("group_id")
CUSTOM_TEMPLATE = config_value("custom_template", "Custom")
GITLAB_TOKEN = config_value("GITLAB_TOKEN", strip_quotes=True)
DELETE_BRANCH = config_bool("delete_branch_after_merge")
DEVELOPER_EMAIL = config_value("developer_email", None)
SQUASH_COMMITS = config_bool("squash_commits")
PRODUCTION_PIPELINE_NAME = config_value("production_pipeline_name", "deploy")
PRODUCTION_JOB_NAME = config_value("production_job_name", None)
PRODUCTION_REF = config_value("production_ref", None)
DEFAULT_MAIN_BRANCH = "master"


def load_template_config(path=TEMPLATES_PATH):
    if not Path(path).exists():
        return {"templates": [], "reviewers": [], "productionMappings": {}}
    with open(path, "r", encoding="utf-8") as template_file:
        return json.load(template_file)


TEMPLATE_CONFIG = load_template_config()
TEMPLATES = TEMPLATE_CONFIG.get("templates", [])
REVIEWERS = TEMPLATE_CONFIG.get("reviewers", [])
PRODUCTION_MAPPINGS = TEMPLATE_CONFIG.get("productionMappings", {})
