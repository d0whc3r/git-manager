"""Entry point: `git-manager [folder]`, defaulting to the current folder."""

import sys
from pathlib import Path

from git_manager import __version__
from git_manager.upgrade import upgrade

USAGE = """usage: git-manager [folder]

Scan a folder tree for git repositories and sync them with their default branch.
Defaults to the current folder.

  -h, --help     show this message
  -V, --version  show the version
  --upgrade      replace the installed binary with the latest release
"""


def main():
    """Parse the one optional argument and start the UI. Returns the process exit code."""
    arg = sys.argv[1] if len(sys.argv) > 1 else "."
    if arg in ("-h", "--help"):
        print(USAGE, end="")
        return 0
    if arg in ("-V", "--version"):
        print(f"git-manager {__version__}")
        return 0
    if arg == "--upgrade":
        ok, msg = upgrade(__version__)
        print(f"git-manager: {msg}", file=sys.stdout if ok else sys.stderr)
        return 0 if ok else 1

    # A typo would otherwise open on an empty table with no hint as to why.
    if not Path(arg).is_dir():
        print(f"git-manager: not a folder: {arg}", file=sys.stderr)
        return 1

    from git_manager.ui import GitManager

    GitManager(arg).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
