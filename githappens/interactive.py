"""Interactive prompt helpers."""

from __future__ import annotations

from typing import Any

import inquirer


def choose_from_list(name: str, message: str, choices: list[Any]) -> Any:
    """Prompt for one value from a list and return the selected answer."""
    answer = inquirer.prompt([
        inquirer.List(name, message=message, choices=choices),
    ])
    return answer[name]


def choose_from_checkbox(name: str, message: str, choices: list[Any]) -> list[Any]:
    """Prompt for multiple values from a list and return selected answers."""
    answer = inquirer.prompt([
        inquirer.Checkbox(name, message=message, choices=choices),
    ])
    return answer[name]
