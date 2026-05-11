from __future__ import annotations

import configparser
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class AppConfig:
    root: Path
    base_url: str
    api_url: str
    group_id: str
    custom_template: str
    gitlab_token: str
    delete_branch: bool
    developer_email: str | None
    squash_commits: bool
    production_pipeline_name: str
    production_job_name: str | None
    production_ref: str | None
    openai_api_key: str | None
    incident_project_id: str | None
    templates: list[dict[str, Any]]
    reviewers: list[int]
    production_mappings: dict[str, dict[str, str]]
    main_branch: str = "master"


def _read_bool(parser: configparser.ConfigParser, key: str, default: str = "false") -> bool:
    return parser.get("DEFAULT", key, fallback=default).lower() == "true"


def load_config(root: Path | str = PROJECT_ROOT) -> AppConfig:
    root = Path(root)
    config_dir = root / "configs"
    parser = configparser.ConfigParser()
    config_path = config_dir / "config.ini"
    if not parser.read(config_path):
        raise FileNotFoundError(
            f"Missing {config_path}. Copy configs/config.ini.example to configs/config.ini first."
        )

    templates_path = config_dir / "templates.json"
    try:
        with templates_path.open("r", encoding="utf-8") as f:
            templates_config = json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Missing {templates_path}. Copy configs/templates.json.example to configs/templates.json first."
        ) from exc

    base_url = parser.get("DEFAULT", "base_url")
    return AppConfig(
        root=root,
        base_url=base_url,
        api_url=f"{base_url}/api/v4",
        group_id=parser.get("DEFAULT", "group_id"),
        custom_template=parser.get("DEFAULT", "custom_template"),
        gitlab_token=parser.get("DEFAULT", "GITLAB_TOKEN").strip("\"'"),
        delete_branch=_read_bool(parser, "delete_branch_after_merge"),
        developer_email=parser.get("DEFAULT", "developer_email", fallback=None),
        squash_commits=_read_bool(parser, "squash_commits"),
        production_pipeline_name=parser.get("DEFAULT", "production_pipeline_name", fallback="deploy"),
        production_job_name=parser.get("DEFAULT", "production_job_name", fallback=None),
        production_ref=parser.get("DEFAULT", "production_ref", fallback=None),
        openai_api_key=parser.get("DEFAULT", "OPENAI_API_KEY", fallback=None),
        incident_project_id=parser.get("DEFAULT", "incident_project_id", fallback=None),
        templates=templates_config["templates"],
        reviewers=templates_config.get("reviewers", []),
        production_mappings=templates_config.get("productionMappings", {}),
    )

