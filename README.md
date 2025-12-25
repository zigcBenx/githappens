<div align="center">
  <h1>GitHappens⚡</h1>
  <h2>CLI that lets you open merge requests, file issues, and request reviews without leaving your terminal</h2>
  <img src="https://github.com/user-attachments/assets/f18c0f04-edef-467c-b833-019643642beb" alt="GitHappens demo" />
</div>

## Getting started 🚀

## Installation 🔨

### Prerequisites

- install python3 (make sure to include pip in install)
- Install [glab](https://gitlab.com/gitlab-org/cli)
- Authorize via glab `glab auth login` (you will need Gitlab access token, SSH recomended)
- `pip install inquirer` or `pip3 install inquirer`
- `pip install requests` or `pip3 install requests`

### Setup

- Clone repository to your local machine to whatever destination you want (just don't delete it later)

#### Setup configs

- In configs folder copy example files like so:
  `cp configs/templates.json.example configs/templates.json`
  `cp configs/config.ini.example configs/config.ini`
- In `configs.ini` you have to paste id of your group in Gitlab to `group_id` (This is for fetching milestones and epics)
- You can adjust templates now, or play with them later (however, you have to remove comments from json before running the command).

#### Alias

To run GitHappens script anywhere in filesystem, make sure to create an alias.
Add the following line to your `.bashrc` or `.zshrc` file:
```bash
alias gh='python3 ~/<path-to-githappens-project>/main.py'
```

**Note:** If you're upgrading from an older version, update your alias to point to `main.py` instead of `gitHappens.py`.

Run `source ~/.zshrc` or restart terminal.

## Usage ⚡

### Project selection

- Project selection is made automatically if you run script in same path as your project is located.
- You can specify project id or URL-encoded path as script argument e.g.: `--project_id=123456`
- If no of steps above happen, program will prompt you with question about project_id

#### Issue creation for multiple projects at once

This feature is useful if you have to create issue on both backend and frontend project for same thing.

- You can specify list of ids in `templates.json` file.

```
...
{
  "name": "Feature issue for API and frontend",
  ...
  "projectIds": [123, 456]
}
...
```

### Milestone selection

Milestone is set to current by default. If you want to pick it manually, pass `-m` or `--milestone` flag to the script.

### Issue templates

Issue templates are located in `configs/templates.json`.

**Make sure that names of templates are unique**

### Excluding features

If you don't want to include some settings you use following flags:

- `--no_epic` - no epic will be selected or prompted
- `--no_milestone` - no milestone will be selected or prompted

### Only issue

If you are in a hurry and want to create issue for later without merge request and branch this flag is for you.

- `--only_issue` - no merge request nor branch will be created.
  You can achive same functionality with adding onlyIssue key to `templates.json` file.

```
...
{
  "name": "Feature issue for later",
  ...
  "onlyIssue": true
}
...
```

### Open merge request in browser

You can open merge request for current checked out branch in browser with command:

```
gh open
```

### Git review

You can set default reviewers in templates.json file.

```
...
{
  "templates": [
    ...
  ],
  ...
  "reviewers": [234, 456, 678]
}
...
```

To submit merge request into review run command:

```
gh review
```

To also enable **auto-merge when the pipeline succeeds**, add `--auto_merge` or `-am` flag:

```
gh review –-auto_merge

gh review -am
```
### Manually selecting reviewers

To manually select reviewers for your merge request, use the `--select` flag with the review command:

```
gh review --select
```

You will be prompted with an interactive list of reviewers to choose from.


### Last production deployment

You can check when the last successful production deployment occurred:

```
gh last deploy
```

This command shows information about the most recent successful production deployment including timing, pipeline details, and how long ago it happened.

#### Configuration

To configure production deployment detection, add project-specific mappings to your `templates.json`:

```json
{
  "templates": [...],
  "reviewers": [...],
  "productionMappings": {
    "your_project_id": {
      "stage": "production:deploy",
      "job": "deploy-to-production"
    },
    "another_project_id": {
      "stage": "deploy",
      "job": "production:deploy"
    }
  }
}
```

**Note:** The command only considers deployments with "success" status to ensure accurate last deployment information.

### Flag help

If you run just `gh` (or whatever alias you set) or `gh --help` you will see all available flags and a short explanation.

## Project Structure

GitHappens has been refactored into a modular architecture for better maintainability and testability:

```
githappens/
├── main.py                # Entry point and argument parsing
├── config.py              # Configuration management
├── gitlab_api.py          # GitLab API interactions
├── git_utils.py           # Git operations
├── interactive.py         # User prompts and CLI interactions
├── templates.py           # Template processing
├── ai_code_review.py      # AI code review functionality
├── commands/              # Command-specific modules
│   ├── create_issue.py    # Issue creation workflow
│   ├── review.py          # Review workflow
│   ├── deploy.py          # Deployment checks
│   ├── open_mr.py         # Merge request operations
│   ├── summary.py         # Summary commands
│   └── report.py          # Incident report command
├── tests/                 # Unit tests
│   └── ... test_file.py
└── configs/               # Configuration files
    ├── config.ini
    └── templates.json
```

## Troubleshooting 🪲🔫

### Receiving 401 Unauthorized error

If you get `glab: 401 Unauthorized (HTTP 401)` when using GitHappens, you must repeat `glab auth login`
and then reopen your terminal.

## Contributing 🫂🫶

Every contributor is welcome.
I suggest checking Gitlab's official API documentation: https://docs.gitlab.com/ee/api/merge_requests.html

### Development Setup

1. Clone the repository
2. Recommended: create a virtual env (e.g., venv, pyenv)
3. Install dependencies: `pip install -r requirements.txt`
5. Set up your configuration files (see Setup section above)
6. Optional: run tests `pytest tests/`

### Code Structure Guidelines

- Use the config module for all configuration access
- Add new commands by creating modules in the `commands/` directory
- Write unit tests for new functionality in the `tests/` directory

## Donating 💜

Make sure to check this project on [OpenPledge](https://app.openpledge.io/repositories/zigcBenx/gitHappens).

