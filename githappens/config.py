from dataclasses import dataclass
from pathlib import Path
import configparser
import json


@dataclass
class Settings:
    base_url: str
    api_url: str
    group_id: str
    custom_template: str
    gitlab_token: str
    delete_branch_after_merge: bool
    developer_email: str
    squash_commits: bool
    production_pipeline_name: str
    production_job_name: str
    production_ref: str
    incident_project_id: str
    openai_api_key: str


@dataclass
class AppContext:
    root: Path
    settings: Settings
    templates: list
    reviewers: list
    production_mappings: dict
    main_branch: str = "master"


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_required(parser: configparser.ConfigParser, option: str) -> str:
    try:
        return parser.get("DEFAULT", option)
    except (configparser.NoOptionError, configparser.NoSectionError) as exc:
        raise RuntimeError(
            f"Missing '{option}' in configs/config.ini. "
            "Copy configs/config.ini.example to configs/config.ini and fill it in."
        ) from exc


def _read_bool(parser: configparser.ConfigParser, option: str) -> bool:
    return _read_required(parser, option).lower() == "true"


def load_settings(root: Path | None = None) -> Settings:
    root = root or project_root()
    config_path = root / "configs" / "config.ini"
    parser = configparser.ConfigParser()

    if not parser.read(config_path):
        raise RuntimeError(
            "Missing configs/config.ini. Copy configs/config.ini.example to "
            "configs/config.ini and fill it in before running GitHappens."
        )

    base_url = _read_required(parser, "base_url")
    return Settings(
        base_url=base_url,
        api_url=f"{base_url}/api/v4",
        group_id=_read_required(parser, "group_id"),
        custom_template=_read_required(parser, "custom_template"),
        gitlab_token=_read_required(parser, "GITLAB_TOKEN").strip("\"'"),
        delete_branch_after_merge=_read_bool(parser, "delete_branch_after_merge"),
        developer_email=parser.get("DEFAULT", "developer_email", fallback=None),
        squash_commits=_read_bool(parser, "squash_commits"),
        production_pipeline_name=parser.get(
            "DEFAULT", "production_pipeline_name", fallback="deploy"
        ),
        production_job_name=parser.get("DEFAULT", "production_job_name", fallback=None),
        production_ref=parser.get("DEFAULT", "production_ref", fallback=None),
        incident_project_id=parser.get("DEFAULT", "incident_project_id", fallback=None),
        openai_api_key=parser.get("DEFAULT", "OPENAI_API_KEY", fallback=None),
    )


def load_templates(root: Path | None = None) -> tuple[list, list, dict]:
    root = root or project_root()
    templates_path = root / "configs" / "templates.json"

    if not templates_path.exists():
        raise RuntimeError(
            "Missing configs/templates.json. Copy configs/templates.json.example "
            "to configs/templates.json and remove JSON comments before running."
        )

    with templates_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    return (
        payload.get("templates", []),
        payload.get("reviewers", []),
        payload.get("productionMappings", {}),
    )


def load_context(root: Path | None = None) -> AppContext:
    root = root or project_root()
    settings = load_settings(root)
    templates, reviewers, production_mappings = load_templates(root)
    return AppContext(
        root=root,
        settings=settings,
        templates=templates,
        reviewers=reviewers,
        production_mappings=production_mappings,
    )
