from __future__ import annotations


def print_recent_commits(commits: str):
    if commits:
        print(commits)
    else:
        print("No commits found.")


def generate_smart_summary(runtime, commits: str):
    if not commits:
        return

    openai_api_key = runtime.config.openai_api_key
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
                    "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}",
                },
            ],
        )
    except Exception as exc:
        print(f"Error generating AI summary: {exc}")
        return

    print("\n📋 AI-Generated Summary of Recent Changes:\n")
    print(response.choices[0].message.content)
