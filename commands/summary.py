from config import CONFIG
from git_utils import get_two_weeks_commits


def generate_smart_summary():
    commits = get_two_weeks_commits(return_output=True)
    if not commits:
        return

    openai_api_key = CONFIG.get("DEFAULT", "OPENAI_API_KEY", fallback=None)
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
                {
                    "role": "user",
                    "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}",
                },
            ],
        )

        print("\nAI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as error:
        print(f"Error generating AI summary: {error}")
