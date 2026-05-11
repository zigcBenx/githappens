import json
from functools import lru_cache
from typing import Dict, List, Optional

from .config import TEMPLATES_PATH


@lru_cache(maxsize=None)
def load_templates_config(path: str = str(TEMPLATES_PATH)) -> dict:
    with open(path, "r") as template_file:
        return json.load(template_file)


def get_templates(path: str = str(TEMPLATES_PATH)) -> List[Dict]:
    return load_templates_config(path).get("templates", [])


def get_reviewers(path: str = str(TEMPLATES_PATH)) -> List[int]:
    return load_templates_config(path).get("reviewers", [])


def get_production_mappings(path: str = str(TEMPLATES_PATH)) -> dict:
    return load_templates_config(path).get("productionMappings", {})


def get_issue_settings(
    template_name: str,
    templates: Optional[List[Dict]] = None,
    custom_template: Optional[str] = None,
) -> Dict:
    if template_name == custom_template:
        return {}

    templates = templates if templates is not None else get_templates()
    return next((template for template in templates if template.get("name") == template_name), {})


def normalize_labels(labels):
    return ",".join(labels) if isinstance(labels, list) else labels
