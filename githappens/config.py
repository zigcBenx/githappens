"""Configuration loading for GitHappens."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import configparser
import json
from typing import Any


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from configs/config.ini."""

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


def project_root() -> Path:
    """Return the repository root for this installed checkout."""
    return Path(__file__).resolve().parent.parent


def _bool(value: str | bool | None, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() == "true"


def load_config(root: Path | None = None) -> AppConfig:
    """Load config.ini and expose normalized settings.

    The legacy CLI used module-level globals. Keeping config loading here makes
    it testable and avoids spreading path/configparser logic across commands.
    """
    root = root or project_root()
    parser = configparser.ConfigParser()
    parser.read(root / "configs" / "config.ini")

    base_url = parser.get("DEFAULT", "base_url")
    return AppConfig(
        base_url=base_url,
        api_url=f"{base_url}/api/v4",
        group_id=parser.get("DEFAULT", "group_id"),
        custom_template=parser.get("DEFAULT", "custom_template"),
        gitlab_token=parser.get("DEFAULT", "GITLAB_TOKEN").strip("\"'"),
        delete_branch_after_merge=_bool(parser.get("DEFAULT", "delete_branch_after_merge", fallback="false")),
        developer_email=parser.get("DEFAULT", "developer_email", fallback=None),
        squash_commits=_bool(parser.get("DEFAULT", "squash_commits", fallback="false")),
        production_pipeline_name=parser.get("DEFAULT", "production_pipeline_name", fallback="deploy"),
        production_job_name=parser.get("DEFAULT", "production_job_name", fallback=None),
        production_ref=parser.get("DEFAULT", "production_ref", fallback=None),
    )


def load_template_config(root: Path | None = None) -> dict[str, Any]:
    """Load templates.json from the configs directory."""
    root = root or project_root()
    with (root / "configs" / "templates.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)
