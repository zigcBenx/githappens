# INSTRUCTIONS

## Preresequisits

- install python3 (make sure to include pip in install)
- Install [glab](https://gitlab.com/gitlab-org/cli)
- Authorize via glab `glab auth login` (you will need Gitlab access token)
- `pip install inquirer`

## group selection

Group is automatically set to DEWE WEB (change `group_id` in config file: `config.ini`)


## project selection

- Project selection is made automatically if you run script in same path as your project is located (not working yet).
- You can specify project id or URL-encoded path as script argument e.g.: `python gitHappens.py --project_id=123456`
- If no of steps above happen, program will prompt you with question about project_id

## milestone selection

Milestone is set to current by default. If you want to pick it manually, pass `-m` or `--milestone` flag to the script.

## Issue templates

Issue templates are located in `configs/templates.json`.

**Make sure that names of templates are unique**
