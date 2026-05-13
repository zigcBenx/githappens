from __future__ import annotations

import configparser
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AppConfig:
    base_path: Path
    base_url: str
    api_url: str
    group_id: str
    custom_template: str
    gitlab_token: str
    delete_branch_after_merge: bool
    developer_email: str | None
    squash_commits: bool
    production_pipeline_name: str
    production_job_name: str | None
    production_ref: str | None
    incident_project_id: str | None
    openai_api_key: str | None
    templates: list[dict[str, Any]]
    reviewers: list[int]
    production_mappings: dict[str, dict[str, str]]


def _get_bool(config: configparser.ConfigParser, key: str, default: bool = False) -> bool:
    value = config.get("DEFAULT", key, fallback=str(default))
    return value.strip().lower() == "true"


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip().strip("\"'")
    return value or None


def load_app_config(base_path: Path | str | None = None) -> AppConfig:
    root = Path(base_path) if base_path is not None else Path(__file__).resolve().parents[1]
    config_path = root / "configs" / "config.ini"
    templates_path = root / "configs" / "templates.json"

    parser = configparser.ConfigParser()
    if not parser.read(config_path):
        raise FileNotFoundError(
            f"Missing config file: {config_path}. Copy configs/config.ini.example to configs/config.ini."
        )

    with templates_path.open("r", encoding="utf-8") as file:
        template_config = json.load(file)

    base_url = parser.get("DEFAULT", "base_url")
    return AppConfig(
        base_path=root,
        base_url=base_url,
        api_url=f"{base_url}/api/v4",
        group_id=parser.get("DEFAULT", "group_id"),
        custom_template=parser.get("DEFAULT", "custom_template"),
        gitlab_token=parser.get("DEFAULT", "GITLAB_TOKEN").strip("\"'"),
        delete_branch_after_merge=_get_bool(parser, "delete_branch_after_merge"),
        developer_email=_clean_optional(parser.get("DEFAULT", "developer_email", fallback=None)),
        squash_commits=_get_bool(parser, "squash_commits"),
        production_pipeline_name=parser.get("DEFAULT", "production_pipeline_name", fallback="deploy"),
        production_job_name=_clean_optional(parser.get("DEFAULT", "production_job_name", fallback=None)),
        production_ref=_clean_optional(parser.get("DEFAULT", "production_ref", fallback=None)),
        incident_project_id=_clean_optional(parser.get("DEFAULT", "incident_project_id", fallback=None)),
        openai_api_key=_clean_optional(parser.get("DEFAULT", "OPENAI_API_KEY", fallback=None)),
        templates=template_config["templates"],
        reviewers=template_config["reviewers"],
        production_mappings=template_config.get("productionMappings", {}),
    )
