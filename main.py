"""CLI entrypoint for gitHappens.

The command dispatcher lives here so gitHappens.py can stay a small
backward-compatible executable wrapper. The implementation is delegated to
the legacy command functions while the codebase is split into focused modules.
"""

from legacy import main

__all__ = ["main"]
