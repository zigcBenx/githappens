# INSTRUCTIONS

## Preresequisits

- install python3 (make sure to include pip in install)
- Install [glab](https://gitlab.com/gitlab-org/cli)
- Authorize via glab `glab auth login` (you will need Gitlab access token)
- `pip install inquirer`

## Setup

### Alias 

To run gitHappens script anywhere in filesystem, make sure to create an alias.
Add following line to your `.bashrc` or `.zshrc` file
```alias gh='python3 ~/<path-to-githappens-project>/gitHappens.py'```

### Template config file

Copy example template file: `cp configs/templates.json.example configs/templates.json`

### Config.ini file

Copy config.ini file: `cp configs/config.ini.example configs/config.ini`

Group is set in config file: `config.ini` as `group_id`, this is required setting.



## Project selection

- Project selection is made automatically if you run script in same path as your project is located (not working yet).
- You can specify project id or URL-encoded path as script argument e.g.: `python gitHappens.py --project_id=123456`
- If no of steps above happen, program will prompt you with question about project_id

## Milestone selection

Milestone is set to current by default. If you want to pick it manually, pass `-m` or `--milestone` flag to the script.

## Issue templates

Issue templates are located in `configs/templates.json.example`.
Make sure to copy example file: `cp configs/templates.json.example configs/templates.json`

All changes and customizations must be done in `configs/templates.json` file.
**Make sure that names of templates are unique**
