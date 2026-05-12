#!/usr/bin/env python3
"""Backwards-compatible entry point.

The CLI implementation has been split into modular files (see main.py and
the commands/ package). This shim is kept so existing aliases/scripts that
invoke `gitHappens.py` keep working.
"""
from main import main

if __name__ == '__main__':
    main()
