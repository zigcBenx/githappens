import json

import config


def test_load_template_config_returns_defaults_for_missing_file(tmp_path):
    missing_path = tmp_path / "missing.json"

    assert config.load_template_config(missing_path) == {
        "templates": [],
        "reviewers": [],
        "productionMappings": {},
    }


def test_load_template_config_reads_templates(tmp_path):
    template_path = tmp_path / "templates.json"
    payload = {"templates": [{"name": "Bug"}], "reviewers": [1], "productionMappings": {}}
    template_path.write_text(json.dumps(payload), encoding="utf-8")

    assert config.load_template_config(template_path) == payload
