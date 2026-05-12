from .. import git_utils


def print_commit_summary(ctx):
    git_utils.get_two_weeks_commits(ctx)


def generate_smart_summary(ctx):
    commits = git_utils.get_two_weeks_commits(ctx, return_output=True)
    if not commits:
        return

    if not ctx.settings.openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Please install it using: pip install openai")
        return

    openai.api_key = ctx.settings.openai_api_key

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that summarizes git commits. "
                        "Provide a concise, well-organized summary of the main "
                        "changes and themes."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Please summarize these git commits in a clear, bulleted "
                        f"format:\n\n{commits}"
                    ),
                },
            ],
        )
        print("\nAI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as exc:
        print(f"Error generating AI summary: {exc}")
