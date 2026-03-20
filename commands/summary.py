import datetime
import subprocess

import config


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime('%Y-%m-%d')

    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    if (config.DEVELOPER_EMAIL):
        cmd = f'{cmd} | grep {config.DEVELOPER_EMAIL}'
    try:
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, universal_newlines=True).strip()
        if output:
            if return_output:
                return output
            print(output)
        else:
            print("No commits found.")
            return "" if return_output else None
    except subprocess.CalledProcessError as e:
        print(f"No commits were found or an error occurred. (exit status {e.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None


def generate_smart_summary():
    commits = get_two_weeks_commits(return_output=True)
    if not commits:
        return

    # Check if OpenAI API key is set
    openai_api_key = config.ini.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
    if not openai_api_key:
        print("OpenAI API key not set. Skipping AI summary generation.")
        return

    # Dynamically import openai only if API key is present
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
                {"role": "system", "content": "You are a helpful assistant that summarizes git commits. Provide a concise, well-organized summary of the main changes and themes."},
                {"role": "user", "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}"}
            ]
        )

        print("\n📋 AI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating AI summary: {e}")
