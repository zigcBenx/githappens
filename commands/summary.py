import git_utils


def generate_smart_summary(settings):
    commits = git_utils.get_two_weeks_commits(
        developer_email=settings.developer_email,
        return_output=True,
    )
    if not commits:
        return

    if not settings.openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    try:
        import openai
    except ImportError:
        print("OpenAI package not installed. Please install it using: pip install openai")
        return

    openai.api_key = settings.openai_api_key

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
