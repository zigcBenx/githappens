import configparser
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "configs")
DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "config.ini")
DEFAULT_TEMPLATES_PATH = os.path.join(CONFIG_DIR, "templates.json")


@dataclass(frozen=True)
class AppSettings:
    base_url: str
    group_id: str
    custom_template: str
    gitlab_token: str
    delete_branch: bool
    developer_email: Optional[str]
    squash_commits: bool
    production_pipeline_name: str
    production_job_name: Optional[str]
    production_ref: Optional[str]
    openai_api_key: Optional[str]
    incident_project_id: Optional[str]
    templates: List[Dict[str, Any]]
    reviewers: List[int]
    production_mappings: Dict[str, Dict[str, str]]
    config_path: str = DEFAULT_CONFIG_PATH
    templates_path: str = DEFAULT_TEMPLATES_PATH

    @property
    def api_url(self) -> str:
        return self.base_url.rstrip("/") + "/api/v4"


def _required(parser: configparser.ConfigParser, option: str) -> str:
    return parser.get("DEFAULT", option)


def _optional(parser: configparser.ConfigParser, option: str) -> Optional[str]:
    value = parser.get("DEFAULT", option, fallback=None)
    if value == "":
        return None
    return value


def _read_ini(path: str) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    if not parser.read(path):
        raise FileNotFoundError(
            f"Missing config file: {path}. Copy configs/config.ini.example to configs/config.ini first."
        )
    return parser


def _read_templates(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing templates file: {path}. Copy configs/templates.json.example to configs/templates.json first."
        )
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_settings(
    config_path: Optional[str] = None,
    templates_path: Optional[str] = None,
) -> AppSettings:
    config_path = config_path or os.environ.get("GITHAPPENS_CONFIG", DEFAULT_CONFIG_PATH)
    templates_path = templates_path or os.environ.get("GITHAPPENS_TEMPLATES", DEFAULT_TEMPLATES_PATH)

    parser = _read_ini(config_path)
    templates_config = _read_templates(templates_path)

    return AppSettings(
        base_url=_required(parser, "base_url"),
        group_id=_required(parser, "group_id"),
        custom_template=_required(parser, "custom_template"),
        gitlab_token=_required(parser, "GITLAB_TOKEN").strip("\"'"),
        delete_branch=parser.get("DEFAULT", "delete_branch_after_merge").lower() == "true",
        developer_email=_optional(parser, "developer_email"),
        squash_commits=parser.get("DEFAULT", "squash_commits").lower() == "true",
        production_pipeline_name=parser.get("DEFAULT", "production_pipeline_name", fallback="deploy"),
        production_job_name=_optional(parser, "production_job_name"),
        production_ref=_optional(parser, "production_ref"),
        openai_api_key=_optional(parser, "OPENAI_API_KEY"),
        incident_project_id=_optional(parser, "incident_project_id"),
        templates=templates_config.get("templates", []),
        reviewers=templates_config.get("reviewers", []),
        production_mappings=templates_config.get("productionMappings", {}),
        config_path=config_path,
        templates_path=templates_path,
    )
