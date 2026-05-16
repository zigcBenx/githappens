from __future__ import annotations

import configparser

from ..config import AppConfig
from ..git_utils import get_two_weeks_commits


def print_recent_commits(config: AppConfig) -> None:
    get_two_weeks_commits(config.developer_email)


def generate_smart_summary(config: AppConfig) -> None:
    commits = get_two_weeks_commits(config.developer_email, return_output=True)
    if not commits:
        return

    parser = configparser.ConfigParser()
    parser.read(config.base_dir / "configs" / "config.ini")
    openai_api_key = parser.get("DEFAULT", "OPENAI_API_KEY", fallback=None)
    if not openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Please install it using: pip install openai")
        return

    openai.api_key = openai_api_key
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes git commits. Provide a concise, well-organized summary of the main changes and themes.",
                },
                {"role": "user", "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}"},
            ],
        )
        print("\nAI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as error:
        print(f"Error generating AI summary: {error}")
