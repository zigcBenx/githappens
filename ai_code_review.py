#!/usr/bin/env python3
import subprocess
import json
import sys
import os
import configparser

# ANSI color codes
class Colors:
    CRITICAL = '\033[91m'  # Red
    HIGH = '\033[93m'      # Yellow
    MEDIUM = '\033[94m'    # Blue
    LOW = '\033[92m'       # Green
    INFO = '\033[96m'      # Cyan
    BOLD = '\033[1m'
    RESET = '\033[0m'
    DIM = '\033[2m'

SYSTEM_PROMPT = """You are a senior code reviewer performing a thorough code review. Analyze the provided git diff and identify issues.

**CRITICAL RULES:**
1. Output ONLY valid JSON - no markdown, no code blocks, no explanations
2. Focus on actual problems in the code, not style preferences
3. Be concise and actionable
4. If no issues found, return empty arrays
5. Extract EXACT line numbers from the diff (look for +line_number or new_line markers)

**Output format (pure JSON only):**
{
  "critical": [{"file": "path/to/file", "line": numeric_line_number, "issue": "brief description"}],
  "high": [{"file": "path/to/file", "line": numeric_line_number, "issue": "brief description"}],
  "medium": [{"file": "path/to/file", "line": numeric_line_number, "issue": "brief description"}],
  "low": [{"file": "path/to/file", "line": numeric_line_number, "issue": "brief description"}],
  "summary": "one-sentence overall assessment"
}

**IMPORTANT:**
- "line" must be a NUMBER (not string like "10-15" or "approx 20")
- "file" must be the exact file path from the diff
- Use the NEW line number (after changes) from the diff header

**Severity guidelines:**
- CRITICAL: Security vulnerabilities, data loss, crashes, exposed secrets
- HIGH: Logic errors, race conditions, resource leaks, incorrect algorithms
- MEDIUM: Code smells, potential bugs, missing error handling
- LOW: Minor improvements, suggestions, style inconsistencies"""

def get_branch_diff():
    """Get the diff of changed files in current branch vs main branch."""
    try:
        # Get main branch name
        main_branch = subprocess.check_output(
            "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'",
            shell=True, text=True, stderr=subprocess.STDOUT
        ).strip()
    except subprocess.CalledProcessError:
        main_branch = 'master'

    try:
        current_branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            text=True
        ).strip()

        if current_branch == main_branch:
            print(f"{Colors.HIGH}⚠ You are on the main branch ({main_branch}). No changes to review.{Colors.RESET}")
            return None

        # Get diff of changed files only
        diff_output = subprocess.check_output(
            ['git', 'diff', f'{main_branch}...HEAD'],
            text=True,
            stderr=subprocess.DEVNULL
        )

        if not diff_output.strip():
            print(f"{Colors.INFO}ℹ No changes detected between {current_branch} and {main_branch}{Colors.RESET}")
            return None

        return diff_output

    except subprocess.CalledProcessError as e:
        print(f"{Colors.CRITICAL}✗ Error getting git diff: {e}{Colors.RESET}")
        return None

def get_openai_client():
    """Initialize OpenAI client with API key from config."""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configs/config.ini')
    config.read(config_path)

    api_key = config.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
    if not api_key:
        print(f"{Colors.HIGH}⚠ OpenAI API key not set in configs/config.ini{Colors.RESET}")
        print(f"{Colors.DIM}  Add: OPENAI_API_KEY = your_key_here{Colors.RESET}")
        return None

    try:
        import openai
        openai.api_key = api_key
        return openai
    except ImportError:
        print(f"{Colors.HIGH}⚠ OpenAI package not installed{Colors.RESET}")
        print(f"{Colors.DIM}  Install: pip install openai{Colors.RESET}")
        return None

def review_code(diff_content):
    """Send code diff to OpenAI for review."""
    openai = get_openai_client()
    if not openai:
        return None

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Review this git diff:\n\n{diff_content}"}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError as e:
        print(f"{Colors.CRITICAL}✗ Failed to parse AI response as JSON{Colors.RESET}")
        print(f"{Colors.DIM}Error: {e}{Colors.RESET}")
        return None
    except Exception as e:
        print(f"{Colors.CRITICAL}✗ Error during AI review: {e}{Colors.RESET}")
        return None

def print_issues(issues, severity, color, icon):
    """Print issues with consistent formatting."""
    if not issues:
        return

    print(f"\n{color}{Colors.BOLD}{icon} {severity.upper()}{Colors.RESET}")
    for issue in issues:
        file_path = issue.get('file', 'unknown')
        line = issue.get('line', '?')
        description = issue.get('issue', 'No description')
        print(f"  {color}•{Colors.RESET} {Colors.BOLD}{file_path}:{line}{Colors.RESET}")
        print(f"    {description}")

def display_review_results(results):
    """Display code review results in a clean, colored format."""
    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}  AI CODE REVIEW{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.RESET}")

    # Count total issues
    total = sum([
        len(results.get('critical', [])),
        len(results.get('high', [])),
        len(results.get('medium', [])),
        len(results.get('low', []))
    ])

    if total == 0:
        print(f"\n{Colors.INFO}{Colors.BOLD}✓ No issues found!{Colors.RESET}")
        print(f"{Colors.DIM}  Code looks good to merge.{Colors.RESET}")
    else:
        print(f"\n{Colors.BOLD}Found {total} issue(s):{Colors.RESET}")

        print_issues(results.get('critical', []), 'critical', Colors.CRITICAL, '🔴')
        print_issues(results.get('high', []), 'high', Colors.HIGH, '🟡')
        print_issues(results.get('medium', []), 'medium', Colors.MEDIUM, '🔵')
        print_issues(results.get('low', []), 'low', Colors.LOW, '🟢')

    # Print summary if available
    summary = results.get('summary', '')
    if summary:
        print(f"\n{Colors.BOLD}Summary:{Colors.RESET}")
        print(f"  {Colors.DIM}{summary}{Colors.RESET}")

    print(f"\n{Colors.BOLD}{'=' * 70}{Colors.RESET}\n")

def format_gitlab_comment(results):
    """Format review results as a GitLab markdown comment."""
    total = sum([
        len(results.get('critical', [])),
        len(results.get('high', [])),
        len(results.get('medium', [])),
        len(results.get('low', []))
    ])

    if total == 0:
        return "## 🤖 AI Code Review\n\n✅ **No issues found!** Code looks good to merge."

    comment = "## 🤖 AI Code Review\n\n"
    comment += f"**Found {total} issue(s)**\n\n"

    def format_issues(issues, severity, emoji):
        if not issues:
            return ""
        section = f"### {emoji} {severity.upper()}\n\n"
        for issue in issues:
            file_path = issue.get('file', 'unknown')
            line = issue.get('line', '?')
            description = issue.get('issue', 'No description')
            section += f"- **`{file_path}:{line}`** - {description}\n"
        return section + "\n"

    comment += format_issues(results.get('critical', []), 'Critical', '🔴')
    comment += format_issues(results.get('high', []), 'High', '🟡')
    comment += format_issues(results.get('medium', []), 'Medium', '🔵')
    comment += format_issues(results.get('low', []), 'Low', '🟢')

    summary = results.get('summary', '')
    if summary:
        comment += f"---\n**Summary:** {summary}\n"

    return comment

def get_merge_request_changes(project_id, mr_id, gitlab_token, api_url):
    """Get the changes (diffs) from the merge request to find commit SHAs."""
    import requests

    url = f"{api_url}/projects/{project_id}/merge_requests/{mr_id}/changes"
    headers = {"Private-Token": gitlab_token}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{Colors.CRITICAL}✗ Failed to get MR changes: {response.status_code}{Colors.RESET}")
            return None
    except Exception as e:
        print(f"{Colors.CRITICAL}✗ Error getting MR changes: {e}{Colors.RESET}")
        return None

def get_diff_refs(project_id, mr_id, gitlab_token, api_url):
    """Get the diff refs (base_sha, head_sha, start_sha) from the merge request."""
    import requests

    url = f"{api_url}/projects/{project_id}/merge_requests/{mr_id}"
    headers = {"Private-Token": gitlab_token}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            mr_data = response.json()
            diff_refs = mr_data.get('diff_refs', {})
            return {
                'base_sha': diff_refs.get('base_sha'),
                'head_sha': diff_refs.get('head_sha'),
                'start_sha': diff_refs.get('start_sha')
            }
        return None
    except Exception:
        return None

def post_inline_comment(issue, severity, project_id, mr_id, gitlab_token, api_url, diff_refs):
    """Post an inline comment on a specific line in the merge request."""
    import requests

    url = f"{api_url}/projects/{project_id}/merge_requests/{mr_id}/discussions"
    headers = {"Private-Token": gitlab_token}

    severity_emoji = {
        'critical': '🔴',
        'high': '🟡',
        'medium': '🔵',
        'low': '🟢'
    }

    emoji = severity_emoji.get(severity, '⚪')
    body = f"{emoji} **{severity.upper()}**: {issue['issue']}"

    file_path = issue['file']
    line = issue['line']

    # Convert line to integer if it's a string
    try:
        line = int(line) if isinstance(line, str) else line
    except (ValueError, TypeError):
        print(f"{Colors.HIGH}⚠ Skipping comment (invalid line number): {file_path}:{line}{Colors.RESET}")
        return False

    data = {
        "body": body,
        "position": {
            "base_sha": diff_refs['base_sha'],
            "head_sha": diff_refs['head_sha'],
            "start_sha": diff_refs['start_sha'],
            "position_type": "text",
            "new_path": file_path,
            "new_line": line
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            return True
        else:
            # Print error details for debugging
            error_msg = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"{Colors.DIM}  Failed {file_path}:{line} - {response.status_code}: {error_msg}{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.DIM}  Error posting inline comment: {e}{Colors.RESET}")
        return False

def post_to_merge_request(comment_body, project_id, mr_id, gitlab_token, api_url):
    """Post AI review as a general comment on the GitLab merge request."""
    import requests

    url = f"{api_url}/projects/{project_id}/merge_requests/{mr_id}/notes"
    headers = {"Private-Token": gitlab_token}
    data = {"body": comment_body}

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            print(f"{Colors.INFO}✓ AI review summary posted to merge request{Colors.RESET}")
            return True
        else:
            print(f"{Colors.CRITICAL}✗ Failed to post comment: {response.status_code}{Colors.RESET}")
            print(f"{Colors.DIM}{response.text}{Colors.RESET}")
            return False
    except Exception as e:
        print(f"{Colors.CRITICAL}✗ Error posting to GitLab: {e}{Colors.RESET}")
        return False

def run_review():
    """Main entry point for AI code review (terminal output)."""
    print(f"{Colors.INFO}🔍 Analyzing code changes...{Colors.RESET}")

    diff_content = get_branch_diff()
    if not diff_content:
        sys.exit(0)

    print(f"{Colors.INFO}🤖 Running AI code review...{Colors.RESET}")
    results = review_code(diff_content)
    if not results:
        print(f"{Colors.HIGH}⚠ AI review skipped{Colors.RESET}")
        sys.exit(0)
    display_review_results(results)

def run_review_for_mr(project_id, mr_id, gitlab_token, api_url):
    """Run AI code review and post inline comments to GitLab merge request."""
    print(f"{Colors.INFO}🤖 Running AI code review...{Colors.RESET}")

    diff_content = get_branch_diff()
    if not diff_content:
        return

    results = review_code(diff_content)
    if not results:
        print(f"{Colors.HIGH}⚠ AI review skipped{Colors.RESET}")
        return

    # Get diff refs for inline comments
    diff_refs = get_diff_refs(project_id, mr_id, gitlab_token, api_url)
    if not diff_refs or not all(diff_refs.values()):
        print(f"{Colors.HIGH}⚠ Could not get diff refs, posting summary only{Colors.RESET}")
        comment = format_gitlab_comment(results)
        post_to_merge_request(comment, project_id, mr_id, gitlab_token, api_url)
        return

    # Post inline comments for each issue
    total_posted = 0
    failed_comments = []

    for severity in ['critical', 'high', 'medium', 'low']:
        issues = results.get(severity, [])
        for issue in issues:
            success = post_inline_comment(issue, severity, project_id, mr_id, gitlab_token, api_url, diff_refs)
            if success:
                total_posted += 1
                print(f"{Colors.INFO}  ✓ Posted {severity} issue on {issue['file']}:{issue['line']}{Colors.RESET}")
            else:
                failed_comments.append((severity, issue))

    # Post summary comment only if there are failed inline comments
    if failed_comments:
        summary_comment = f"## 🤖 AI Code Review\n\n"
        summary_comment += f"### Issues (could not post inline):\n"
        for severity, issue in failed_comments:
            emoji = {'critical': '🔴', 'high': '🟡', 'medium': '🔵', 'low': '🟢'}.get(severity, '⚪')
            summary_comment += f"- {emoji} **`{issue['file']}:{issue['line']}`** - {issue['issue']}\n"
        post_to_merge_request(summary_comment, project_id, mr_id, gitlab_token, api_url)
    else:
        print(f"{Colors.INFO}✓ All {total_posted} issues posted as inline comments{Colors.RESET}")

if __name__ == '__main__':
    run_review()
