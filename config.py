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
    openai_api_key: str | None = None
    incident_project_id: str | None = None

    @property
    def api_url(self):
        return f"{self.base_url}/api/v4"


def _get(parser, option, fallback=None):
    return parser.get("DEFAULT", option, fallback=fallback)


def _get_bool(parser, option, fallback):
    return _get(parser, option, str(fallback)).lower() == "true"


def load_config(path=CONFIG_PATH):
    parser = configparser.ConfigParser()
    parser.read(path)
    return AppConfig(
        base_url=_get(parser, "base_url", "https://gitlab.com"),
        group_id=_get(parser, "group_id", ""),
        custom_template=_get(parser, "custom_template", "Custom"),
        gitlab_token=_get(parser, "GITLAB_TOKEN", "").strip("\"'"),
        delete_branch_after_merge=_get_bool(parser, "delete_branch_after_merge", True),
        developer_email=_get(parser, "developer_email", None),
        squash_commits=_get_bool(parser, "squash_commits", True),
        production_pipeline_name=_get(parser, "production_pipeline_name", "deploy"),
        production_job_name=_get(parser, "production_job_name", None),
        production_ref=_get(parser, "production_ref", None),
        openai_api_key=_get(parser, "OPENAI_API_KEY", None),
        incident_project_id=_get(parser, "incident_project_id", None),
    )


def load_template_config(path=TEMPLATES_PATH):
    if not Path(path).exists():
        return {"templates": [], "reviewers": [], "productionMappings": {}}

    with open(path, "r") as file:
        data = json.load(file)

    return {
        "templates": data.get("templates", []),
        "reviewers": data.get("reviewers", []),
        "productionMappings": data.get("productionMappings", {}),
    }


CONFIG = load_config()
TEMPLATE_CONFIG = load_template_config()
TEMPLATES = TEMPLATE_CONFIG["templates"]
REVIEWERS = TEMPLATE_CONFIG["reviewers"]
PRODUCTION_MAPPINGS = TEMPLATE_CONFIG["productionMappings"]
