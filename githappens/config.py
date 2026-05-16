from __future__ import annotations

import configparser
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    base_dir: Path
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
    templates: list[dict[str, Any]]
    reviewers: list[int]
    production_mappings: dict[str, dict[str, str]]
    main_branch: str = "master"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _config_path(base_dir: Path) -> Path:
    return base_dir / "configs" / "config.ini"


def _templates_path(base_dir: Path) -> Path:
    return base_dir / "configs" / "templates.json"


def _missing_config_message(path: Path) -> str:
    return (
        f"Missing required config file: {path}\n"
        "Copy configs/config.ini.example to configs/config.ini and fill in the required values."
    )


def load_app_config(base_dir: str | Path | None = None) -> AppConfig:
    root = Path(base_dir) if base_dir is not None else project_root()
    parser = configparser.ConfigParser()
    config_file = _config_path(root)

    if not config_file.exists():
        raise RuntimeError(_missing_config_message(config_file))

    parser.read(config_file)
    templates_file = _templates_path(root)
    if not templates_file.exists():
        raise RuntimeError(
            f"Missing required templates file: {templates_file}\n"
            "Copy configs/templates.json.example to configs/templates.json and remove JSON comments."
        )

    with templates_file.open(encoding="utf-8") as file:
        template_config = json.load(file)

    base_url = parser.get("DEFAULT", "base_url")

    return AppConfig(
        base_dir=root,
        base_url=base_url,
        api_url=f"{base_url}/api/v4",
        group_id=parser.get("DEFAULT", "group_id"),
        custom_template=parser.get("DEFAULT", "custom_template"),
        gitlab_token=parser.get("DEFAULT", "GITLAB_TOKEN").strip("\"'"),
        delete_branch=parser.getboolean("DEFAULT", "delete_branch_after_merge", fallback=True),
        developer_email=parser.get("DEFAULT", "developer_email", fallback=None),
        squash_commits=parser.getboolean("DEFAULT", "squash_commits", fallback=True),
        production_pipeline_name=parser.get("DEFAULT", "production_pipeline_name", fallback="deploy"),
        production_job_name=parser.get("DEFAULT", "production_job_name", fallback=None) or None,
        production_ref=parser.get("DEFAULT", "production_ref", fallback=None) or None,
        templates=template_config.get("templates", []),
        reviewers=template_config.get("reviewers", []),
        production_mappings=template_config.get("productionMappings", {}),
    )
