import configparser

import config


def test_config_exports_expected_constants():
    assert config.BASE_URL == "https://gitlab.test"
    assert config.API_URL == "https://gitlab.test/api/v4"
    assert config.GROUP_ID == "99"
    assert config.CUSTOM_TEMPLATE == "CustomTmpl"
    assert config.GITLAB_TOKEN == "test-token"
    assert config.DELETE_BRANCH is False
    assert config.SQUASH_COMMITS is False
    assert config.PRODUCTION_PIPELINE_NAME == "deploy"
    assert "Bug" in [t["name"] for t in config.TEMPLATES]
    assert config.REVIEWERS == [101, 102]
    assert isinstance(config.PRODUCTION_MAPPINGS, dict)


def test_set_main_branch_updates_main_branch():
    try:
        config.set_main_branch("develop")
        assert config.MAIN_BRANCH == "develop"
    finally:
        config.set_main_branch("master")


def test_ini_is_config_parser():
    assert isinstance(config.ini, configparser.ConfigParser)
