"""Entry point: `git-manager [folder]`, defaulting to the current folder."""

import sys

from git_manager import __version__

USAGE = """usage: git-manager [folder]

Scan a folder tree for git repositories and sync them with their default branch.
Defaults to the current folder.

  -h, --help     show this message
  -V, --version  show the version
"""


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "."
    if arg in ("-h", "--help"):
        print(USAGE, end="")
        return
    if arg in ("-V", "--version"):
        print(f"git-manager {__version__}")
        return

    from git_manager.ui import GitManager

    GitManager(arg).run()


if __name__ == "__main__":
    main()
