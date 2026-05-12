import configparser
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "configs"


def _read_config():
    parser = configparser.ConfigParser()
    config_path = CONFIG_DIR / "config.ini"
    fallback_path = CONFIG_DIR / "config.ini.example"
    parser.read(config_path if config_path.exists() else fallback_path)
    return parser


def _read_json_with_comments(path):
    lines = []
    with path.open("r", encoding="utf-8") as config_file:
        for line in config_file:
            if line.lstrip().startswith("//"):
                continue
            lines.append(line)
    return json.loads("".join(lines))


def _read_templates():
    template_path = CONFIG_DIR / "templates.json"
    fallback_path = CONFIG_DIR / "templates.json.example"
    return _read_json_with_comments(template_path if template_path.exists() else fallback_path)


config = _read_config()
json_config = _read_templates()

BASE_URL = config.get("DEFAULT", "base_url", fallback="https://gitlab.com")
API_URL = f"{BASE_URL}/api/v4"
GROUP_ID = config.get("DEFAULT", "group_id", fallback="")
CUSTOM_TEMPLATE = config.get("DEFAULT", "custom_template", fallback="Custom")
GITLAB_TOKEN = config.get("DEFAULT", "GITLAB_TOKEN", fallback="").strip("\"'")
DELETE_BRANCH = config.get("DEFAULT", "delete_branch_after_merge", fallback="false").lower() == "true"
DEVELOPER_EMAIL = config.get("DEFAULT", "developer_email", fallback=None)
SQUASH_COMMITS = config.get("DEFAULT", "squash_commits", fallback="false").lower() == "true"
PRODUCTION_PIPELINE_NAME = config.get("DEFAULT", "production_pipeline_name", fallback="deploy")
PRODUCTION_JOB_NAME = config.get("DEFAULT", "production_job_name", fallback=None)
PRODUCTION_REF = config.get("DEFAULT", "production_ref", fallback=None)
PRODUCTION_MAPPINGS = json_config.get("productionMappings", {})
TEMPLATES = json_config.get("templates", [])
REVIEWERS = json_config.get("reviewers", [])

MAIN_BRANCH = "master"

