"""Deployment checks command."""
from gitlab_api import get_last_production_deploy


def handle_deploy_command():
    """Handle the last deploy command."""
    get_last_production_deploy()

