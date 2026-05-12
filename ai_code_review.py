#!/usr/bin/env python3
import json
import sys

import config
import git_utils
import gitlab_api

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


def get_openai_client():
    """Initialize OpenAI client with API key from config."""
    api_key = config.config.get('DEFAULT', 'OPENAI_API_KEY', fallback=None)
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

def run_review():
    """Main entry point for AI code review (terminal output)."""
    print(f"{Colors.INFO}🔍 Analyzing code changes...{Colors.RESET}")

    diff_content = git_utils.get_branch_diff()
    if not diff_content:
        sys.exit(0)

    print(f"{Colors.INFO}🤖 Running AI code review...{Colors.RESET}")
    results = review_code(diff_content)
    if not results:
        print(f"{Colors.HIGH}⚠ AI review skipped{Colors.RESET}")
        sys.exit(0)
    display_review_results(results)


def run_review_for_mr(project_id, mr_id):
    """Run AI code review and post inline comments to GitLab merge request."""
    print(f"{Colors.INFO}🤖 Running AI code review...{Colors.RESET}")

    diff_content = git_utils.get_branch_diff()
    if not diff_content:
        return

    results = review_code(diff_content)
    if not results:
        print(f"{Colors.HIGH}⚠ AI review skipped{Colors.RESET}")
        return

    # Get diff refs for inline comments
    diff_refs = gitlab_api.get_diff_refs(project_id, mr_id)
    if not diff_refs or not all(diff_refs.values()):
        print(f"{Colors.HIGH}⚠ Could not get diff refs, posting summary only{Colors.RESET}")
        comment = format_gitlab_comment(results)
        gitlab_api.post_to_merge_request(comment, project_id, mr_id)
        return

    # Post inline comments for each issue
    total_posted = 0
    failed_comments = []

    for severity in ['critical', 'high', 'medium', 'low']:
        issues = results.get(severity, [])
        for issue in issues:
            file_path = issue['file']
            line = issue['line']
            try:
                line = int(line) if isinstance(line, str) else line
            except (ValueError, TypeError):
                print(f"{Colors.HIGH}⚠ Skipping comment (invalid line number): {file_path}:{line}{Colors.RESET}")
                continue

            emoji = {'critical': '🔴', 'high': '🟡', 'medium': '🔵', 'low': '🟢'}.get(severity, '⚪')
            body = f"{emoji} **{severity.upper()}**: {issue['issue']}"
            success = gitlab_api.post_inline_comment(project_id, mr_id, body, diff_refs, file_path, line)
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
        gitlab_api.post_to_merge_request(summary_comment, project_id, mr_id)
    else:
        print(f"{Colors.INFO}✓ All {total_posted} issues posted as inline comments{Colors.RESET}")

if __name__ == '__main__':
    run_review()
