import configparser
import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(ROOT_DIR, "configs")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.ini")
TEMPLATES_PATH = os.path.join(CONFIG_DIR, "templates.json")


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_url: str
    group_id: str
    custom_template: str
    gitlab_token: str
    delete_branch: bool
    developer_email: Optional[str]
    squash_commits: bool
    production_pipeline_name: str
    production_job_name: Optional[str]
    production_ref: Optional[str]
    incident_project_id: Optional[str]


def _read_config(path: Optional[str] = None) -> configparser.ConfigParser:
    if path is None:
        path = CONFIG_PATH
    config = configparser.ConfigParser()
    if not config.read(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    return config


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    config = _read_config()
    base_url = config.get("DEFAULT", "base_url")
    return Settings(
        base_url=base_url,
        api_url=base_url + "/api/v4",
        group_id=config.get("DEFAULT", "group_id"),
        custom_template=config.get("DEFAULT", "custom_template"),
        gitlab_token=config.get("DEFAULT", "GITLAB_TOKEN").strip("\"'"),
        delete_branch=config.get("DEFAULT", "delete_branch_after_merge").lower() == "true",
        developer_email=config.get("DEFAULT", "developer_email", fallback=None),
        squash_commits=config.get("DEFAULT", "squash_commits").lower() == "true",
        production_pipeline_name=config.get("DEFAULT", "production_pipeline_name", fallback="deploy"),
        production_job_name=config.get("DEFAULT", "production_job_name", fallback=None),
        production_ref=config.get("DEFAULT", "production_ref", fallback=None),
        incident_project_id=config.get("DEFAULT", "incident_project_id", fallback=None),
    )


@lru_cache(maxsize=1)
def get_template_config() -> dict:
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as template_file:
        return json.load(template_file)


def get_templates() -> list[dict]:
    return get_template_config()["templates"]


def get_reviewers() -> list[int]:
    return get_template_config().get("reviewers", [])


def get_production_mappings() -> dict:
    return get_template_config().get("productionMappings", {})
