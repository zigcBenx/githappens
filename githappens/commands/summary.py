import datetime
import subprocess

from ..config import get_settings


def get_two_weeks_commits(return_output=False):
    two_weeks_ago = (datetime.datetime.now() - datetime.timedelta(weeks=2)).strftime("%Y-%m-%d")
    cmd = f'git log --since={two_weeks_ago} --format="%ad - %ae - %s" --date=short | grep -v "Merge branch"'
    developer_email = get_settings().developer_email
    if developer_email:
        cmd = f"{cmd} | grep {developer_email}"
    try:
        output = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL, universal_newlines=True).strip()
        if output:
            if return_output:
                return output
            print(output)
        else:
            print("No commits found.")
            return "" if return_output else None
    except subprocess.CalledProcessError as error:
        print(f"No commits were found or an error occurred. (exit status {error.returncode})")
        return "" if return_output else None
    except FileNotFoundError:
        print("Git is not installed or not found in PATH.")
        return "" if return_output else None


def generate_smart_summary():
    commits = get_two_weeks_commits(return_output=True)
    if not commits:
        return

    openai_api_key = None
    try:
        from ..config import _read_config

        openai_api_key = _read_config().get("DEFAULT", "OPENAI_API_KEY", fallback=None)
    except Exception:
        pass
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
                {"role": "system", "content": "You are a helpful assistant that summarizes git commits. Provide a concise, well-organized summary of the main changes and themes."},
                {"role": "user", "content": f"Please summarize these git commits in a clear, bulleted format:\n\n{commits}"},
            ],
        )
        print("\n📋 AI-Generated Summary of Recent Changes:\n")
        print(response.choices[0].message.content)
    except Exception as error:
        print(f"Error generating AI summary: {error}")
