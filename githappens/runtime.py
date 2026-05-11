from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from githappens.config import AppConfig, CONFIG_DIR, REPO_ROOT, load_config


@dataclass
class AppRuntime:
    config: AppConfig
    templates: list[dict]
    reviewers: list[int]
    production_mappings: dict[str, dict]
    repository_root: Path = REPO_ROOT
    main_branch: str = "master"


def load_templates(templates_path: str | Path | None = None) -> tuple[list[dict], list[int], dict[str, dict]]:
    path = Path(templates_path) if templates_path else CONFIG_DIR / "templates.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing templates file: {path}. Copy configs/templates.json.example to configs/templates.json."
        )

    with path.open("r", encoding="utf-8") as handle:
        parsed = json.load(handle)

    return (
        parsed.get("templates", []),
        parsed.get("reviewers", []),
        parsed.get("productionMappings", {}),
    )


def load_runtime(
    config_path: str | Path | None = None,
    templates_path: str | Path | None = None,
) -> AppRuntime:
    config = load_config(config_path)
    templates, reviewers, production_mappings = load_templates(templates_path)
    return AppRuntime(
        config=config,
        templates=templates,
        reviewers=reviewers,
        production_mappings=production_mappings,
    )
