from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import configparser


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "configs"


@dataclass(frozen=True)
class AppConfig:
    base_url: str
    group_id: str
    custom_template: str
    gitlab_token: str
    squash_commits: bool
    delete_branch_after_merge: bool
    developer_email: str | None
    openai_api_key: str | None
    incident_project_id: str | None
    production_pipeline_name: str
    production_job_name: str | None
    production_ref: str | None

    @property
    def api_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/api/v4"


def _read_bool(parser: configparser.ConfigParser, key: str, default: bool = False) -> bool:
    value = parser.get("DEFAULT", key, fallback=str(default))
    return value.lower() == "true"


def _read_optional(parser: configparser.ConfigParser, key: str) -> str | None:
    value = parser.get("DEFAULT", key, fallback=None)
    if value is None:
        return None

    stripped = value.strip().strip("\"'")
    return stripped or None


def load_config(config_path: str | Path | None = None) -> AppConfig:
    path = Path(config_path) if config_path else CONFIG_DIR / "config.ini"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing config file: {path}. Copy configs/config.ini.example to configs/config.ini."
        )

    parser = configparser.ConfigParser()
    parser.read(path)

    return AppConfig(
        base_url=parser.get("DEFAULT", "base_url"),
        group_id=parser.get("DEFAULT", "group_id"),
        custom_template=parser.get("DEFAULT", "custom_template"),
        gitlab_token=_read_optional(parser, "GITLAB_TOKEN") or "",
        squash_commits=_read_bool(parser, "squash_commits", default=True),
        delete_branch_after_merge=_read_bool(parser, "delete_branch_after_merge", default=True),
        developer_email=_read_optional(parser, "developer_email"),
        openai_api_key=_read_optional(parser, "OPENAI_API_KEY"),
        incident_project_id=_read_optional(parser, "incident_project_id"),
        production_pipeline_name=parser.get(
            "DEFAULT", "production_pipeline_name", fallback="deploy"
        ),
        production_job_name=_read_optional(parser, "production_job_name"),
        production_ref=_read_optional(parser, "production_ref"),
    )
