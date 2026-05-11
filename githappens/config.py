import configparser
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "configs"
CONFIG_PATH = CONFIG_DIR / "config.ini"
TEMPLATES_PATH = CONFIG_DIR / "templates.json"


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_url: str
    group_id: str
    custom_template: str
    gitlab_token: str
    delete_branch_after_merge: bool
    developer_email: Optional[str]
    squash_commits: bool
    production_pipeline_name: str
    production_job_name: Optional[str]
    production_ref: Optional[str]
    incident_project_id: Optional[str]
    openai_api_key: Optional[str]


@lru_cache(maxsize=None)
def get_config(config_path: str = str(CONFIG_PATH)) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read(config_path)
    return parser


def _optional(parser: configparser.ConfigParser, option: str, fallback: Optional[str] = None) -> Optional[str]:
    value = parser.get("DEFAULT", option, fallback=fallback)
    if value is None:
        return None
    value = value.strip()
    return value or None


@lru_cache(maxsize=None)
def get_settings(config_path: str = str(CONFIG_PATH)) -> Settings:
    parser = get_config(config_path)

    base_url = parser.get("DEFAULT", "base_url")
    gitlab_token = parser.get("DEFAULT", "GITLAB_TOKEN").strip("\"'")

    return Settings(
        base_url=base_url,
        api_url=f"{base_url}/api/v4",
        group_id=parser.get("DEFAULT", "group_id"),
        custom_template=parser.get("DEFAULT", "custom_template"),
        gitlab_token=gitlab_token,
        delete_branch_after_merge=parser.get("DEFAULT", "delete_branch_after_merge").lower() == "true",
        developer_email=_optional(parser, "developer_email"),
        squash_commits=parser.get("DEFAULT", "squash_commits").lower() == "true",
        production_pipeline_name=parser.get("DEFAULT", "production_pipeline_name", fallback="deploy"),
        production_job_name=_optional(parser, "production_job_name"),
        production_ref=_optional(parser, "production_ref"),
        incident_project_id=_optional(parser, "incident_project_id"),
        openai_api_key=_optional(parser, "OPENAI_API_KEY"),
    )
