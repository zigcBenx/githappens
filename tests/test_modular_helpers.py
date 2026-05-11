import json
from pathlib import Path

from githappens.config import load_config, load_template_config
from githappens.templates import get_issue_settings, normalize_labels, template_names


def make_config_tree(tmp_path: Path) -> Path:
    configs = tmp_path / "configs"
    configs.mkdir()
    (configs / "config.ini").write_text(
        """
[DEFAULT]
base_url = https://gitlab.example.com
group_id = 42
custom_template = Custom
gitlab_token = 'secret-token'
delete_branch_after_merge = true
squash_commits = false
production_pipeline_name = deploy
""".strip(),
        encoding="utf-8",
    )
    (configs / "templates.json").write_text(
        json.dumps({"templates": [{"name": "Bug", "labels": ["bug"]}], "reviewers": [1]}),
        encoding="utf-8",
    )
    return tmp_path


def test_load_config_normalizes_values(tmp_path):
    root = make_config_tree(tmp_path)

    config = load_config(root)

    assert config.base_url == "https://gitlab.example.com"
    assert config.api_url == "https://gitlab.example.com/api/v4"
    assert config.group_id == "42"
    assert config.gitlab_token == "secret-token"
    assert config.delete_branch_after_merge is True
    assert config.squash_commits is False


def test_load_template_config(tmp_path):
    root = make_config_tree(tmp_path)

    template_config = load_template_config(root)

    assert template_config["templates"][0]["name"] == "Bug"
    assert template_config["reviewers"] == [1]


def test_template_helpers():
    templates = [{"name": "Bug", "labels": ["bug"]}]

    assert template_names(templates, "Custom") == ["Bug", "Custom"]
    assert get_issue_settings("Bug", templates, "Custom") == {"name": "Bug", "labels": ["bug"]}
    assert get_issue_settings("Custom", templates, "Custom") == {}
    assert normalize_labels(["bug", "backend"]) == "bug,backend"
    assert normalize_labels("bug") == "bug"
