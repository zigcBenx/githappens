<div align="center">
  <h1>GitHappens⚡</h1>
  <h2>CLI that lets you open merge requests, file issues, and request reviews without leaving your terminal</h2>
  <img src="https://github.com/user-attachments/assets/f18c0f04-edef-467c-b833-019643642beb" alt="GitHappens demo" />
</div>

## Getting started 🚀

GitHappens wraps the GitLab API so you can create issues, branches, and merge
requests without leaving your terminal. Install the prerequisites below, copy
the example config files, point the CLI at your GitLab group, and you are
ready to run `gh "My new issue"` to scaffold an issue, branch, and merge
request in one step.

## Installation 🔨

### Prerequisites

- Install Python 3 (make sure pip is included in the install).
- Install [glab](https://gitlab.com/gitlab-org/cli).
- Authorize via glab: `glab auth login` (you will need a GitLab access token,
  SSH is recommended).
- `pip install inquirer` or `pip3 install inquirer`.
- `pip install requests` or `pip3 install requests`.

### Setup

- Clone the repository to your local machine at any destination you want (just
  don't delete it later).

#### Setup configs

- In the `configs` folder, copy the example files like so:
  `cp configs/templates.json.example configs/templates.json`
  `cp configs/config.ini.example configs/config.ini`
- In `config.ini`, paste the ID of your GitLab group into `group_id`. This is
  used for fetching milestones and epics.
- You can adjust templates now, or play with them later. If you keep comments
  in `templates.json`, remove them before running the command.

#### Alias

To run the gitHappens script anywhere in your filesystem, create an alias.
Add the following line to your `.bashrc` or `.zshrc` file:

`alias gh='python3 ~/<path-to-githappens-project>/gitHappens.py'`

Run `source ~/.zshrc` or restart your terminal.

## Usage ⚡

### Project selection

- Project selection happens automatically if you run the script in the same
  path as your project.
- You can specify a project ID or URL-encoded path as a script argument, e.g.
  `--project_id=123456`.
- If neither of the steps above happens, the program prompts you for a
  `project_id`.

#### Issue creation for multiple projects at once

This feature is useful if you have to create an issue on both the backend and
the frontend project for the same thing.

- You can specify a list of IDs in the `templates.json` file.

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

The milestone is set to the current one by default. If you want to pick it
manually, pass the `-m` or `--milestone` flag to the script.

### Issue templates

Issue templates are located in `configs/templates.json`.

**Make sure the template names are unique.**

### Excluding features

If you don't want to include some settings, use the following flags:

- `--no_epic` - no epic will be selected or prompted.
- `--no_milestone` - no milestone will be selected or prompted.

### Only issue

If you are in a hurry and want to create an issue for later without a merge
request and branch, this flag is for you.

- `--only_issue` - no merge request or branch will be created.
  You can achieve the same functionality by adding the `onlyIssue` key to the
  `templates.json` file.

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

You can open the merge request for the currently checked-out branch in your
browser with:

```
gh open
```

### Git review

You can set default reviewers in the `templates.json` file.

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

To submit a merge request for review, run:

```
gh review
```

To also enable **auto-merge when the pipeline succeeds**, add the
`--auto_merge` or `-am` flag:

```
gh review --auto_merge

gh review -am
```

### Manually selecting reviewers

To manually select reviewers for your merge request, use the `--select` flag
with the review command:

```
gh review --select
```

You are then prompted with an interactive list of reviewers to choose from.

### Last production deployment

You can check when the last successful production deployment occurred:

```
gh last deploy
```

This command shows information about the most recent successful production
deployment, including timing, pipeline details, and how long ago it happened.

#### Configuration

To configure production deployment detection, add project-specific mappings to
your `templates.json`:

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

**Note:** the command only considers deployments with `success` status to
ensure accurate last-deployment information.

### Flag help

If you run just `gh` (or whatever alias you set) or `gh --help`, you see all
available flags and a short explanation of each.

## Troubleshooting 🪲🔫

### Receiving a 401 Unauthorized error

If you get `glab: 401 Unauthorized (HTTP 401)` when using GitHappens, repeat
`glab auth login` and then reopen your terminal.

## Contributing 🫂🫶

Every contributor is welcome.
We recommend checking GitLab's official API documentation:
<https://docs.gitlab.com/ee/api/merge_requests.html>.

## Donating 💜

Make sure to check this project on
[OpenPledge](https://app.openpledge.io/repositories/zigcBenx/gitHappens).
