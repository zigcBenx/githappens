"""Commit summaries (raw and AI-generated)."""
import config
import git_utils


def show_two_weeks_commits():
    git_utils.get_two_weeks_commits()


def generate_smart_summary():
    commits = git_utils.get_two_weeks_commits(return_output=True)
    if not commits:
        return

    openai_api_key = config.get_openai_api_key()
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
                    "content": (
                        "You are a helpful assistant that summarizes git commits. "
                        "Provide a concise, well-organized summary of the main changes and themes."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Please summarize these git commits in a clear, bulleted format:\n\n"
                        + commits
                    ),
                },
            ],
        )
        print("\n📋 AI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating AI summary: {e}")
