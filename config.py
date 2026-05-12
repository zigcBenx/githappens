from __future__ import annotations

import configparser
import json
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = ROOT_DIR / "configs"
CONFIG_PATH = CONFIG_DIR / "config.ini"
TEMPLATES_PATH = CONFIG_DIR / "templates.json"


@dataclass(frozen=True)
class AppConfig:
    base_url: str = "https://gitlab.com"
    group_id: str = ""
    custom_template: str = "Custom"
    gitlab_token: str = ""
    delete_branch_after_merge: bool = True
    developer_email: str | None = None
    squash_commits: bool = True
    production_pipeline_name: str = "deploy"
    production_job_name: str | None = None
    production_ref: str | None = None
    incident_project_id: str | None = None
    openai_api_key: str | None = None

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/api/v4"


@dataclass(frozen=True)
class TemplateConfig:
    templates: list
    reviewers: list
    production_mappings: dict


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().strip("\"'")
    return value or None


def _get_bool(parser: configparser.ConfigParser, option: str, fallback: bool) -> bool:
    return parser.get("DEFAULT", option, fallback=str(fallback)).lower() == "true"


def load_config_parser(config_path: Path | str = CONFIG_PATH) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read(config_path)
    return parser


def load_app_config(config_path: Path | str = CONFIG_PATH) -> AppConfig:
    parser = load_config_parser(config_path)
    return AppConfig(
        base_url=parser.get("DEFAULT", "base_url", fallback="https://gitlab.com"),
        group_id=parser.get("DEFAULT", "group_id", fallback=""),
        custom_template=parser.get("DEFAULT", "custom_template", fallback="Custom"),
        gitlab_token=_clean_optional(parser.get("DEFAULT", "GITLAB_TOKEN", fallback="")) or "",
        delete_branch_after_merge=_get_bool(parser, "delete_branch_after_merge", True),
        developer_email=_clean_optional(parser.get("DEFAULT", "developer_email", fallback=None)),
        squash_commits=_get_bool(parser, "squash_commits", True),
        production_pipeline_name=parser.get("DEFAULT", "production_pipeline_name", fallback="deploy"),
        production_job_name=_clean_optional(parser.get("DEFAULT", "production_job_name", fallback=None)),
        production_ref=_clean_optional(parser.get("DEFAULT", "production_ref", fallback=None)),
        incident_project_id=_clean_optional(parser.get("DEFAULT", "incident_project_id", fallback=None)),
        openai_api_key=_clean_optional(parser.get("DEFAULT", "OPENAI_API_KEY", fallback=None)),
    )


def load_template_config(templates_path: Path | str = TEMPLATES_PATH) -> TemplateConfig:
    path = Path(templates_path)
    if not path.exists():
        return TemplateConfig(templates=[], reviewers=[], production_mappings={})

    with path.open("r", encoding="utf-8") as f:
        json_config = json.load(f)

    return TemplateConfig(
        templates=json_config.get("templates", []),
        reviewers=json_config.get("reviewers", []),
        production_mappings=json_config.get("productionMappings", {}),
    )


APP_CONFIG = load_app_config()
TEMPLATE_CONFIG = load_template_config()
CONFIG_PARSER = load_config_parser()

BASE_URL = APP_CONFIG.base_url
API_URL = APP_CONFIG.api_url
GROUP_ID = APP_CONFIG.group_id
CUSTOM_TEMPLATE = APP_CONFIG.custom_template
GITLAB_TOKEN = APP_CONFIG.gitlab_token
DELETE_BRANCH = APP_CONFIG.delete_branch_after_merge
DEVELOPER_EMAIL = APP_CONFIG.developer_email
SQUASH_COMMITS = APP_CONFIG.squash_commits
PRODUCTION_PIPELINE_NAME = APP_CONFIG.production_pipeline_name
PRODUCTION_JOB_NAME = APP_CONFIG.production_job_name
PRODUCTION_REF = APP_CONFIG.production_ref
INCIDENT_PROJECT_ID = APP_CONFIG.incident_project_id
OPENAI_API_KEY = APP_CONFIG.openai_api_key
MAIN_BRANCH = "master"

TEMPLATES = TEMPLATE_CONFIG.templates
REVIEWERS = TEMPLATE_CONFIG.reviewers
PRODUCTION_MAPPINGS = TEMPLATE_CONFIG.production_mappings
