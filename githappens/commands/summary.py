from __future__ import annotations

from .. import git_utils
from ..config import AppConfig


def generate_smart_summary(config: AppConfig):
    commits = git_utils.get_two_weeks_commits(config.developer_email, return_output=True)
    if not commits:
        return
    if not config.openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Please install it using: pip install openai")
        return

    openai.api_key = config.openai_api_key
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
        print("\n📋 AI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating AI summary: {e}")

