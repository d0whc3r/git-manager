"""Self-upgrade: replace the installed release binary with the newest published one.

The download is handed to the same `install.sh` the project documents, so platform
detection, the atomic replacement and the macOS quarantine flag live in one place only.
"""

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = "d0whc3r/git-manager"
LATEST_RELEASE_API = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_PAGE = f"https://github.com/{REPO}/releases/latest"

#: Fetch the documented installer and run it. No user input reaches this command; the
#: install location is passed out of band, through BIN_DIR in the environment.
INSTALL_COMMAND = f"curl -fsSL https://raw.githubusercontent.com/{REPO}/main/install.sh | sh"

#: Seconds the release lookup may take. One small JSON response.
API_TIMEOUT = 15

#: Seconds the download may take. The binaries embed CPython and are tens of megabytes.
DOWNLOAD_TIMEOUT = 600


def latest_version():
    """Version of the newest published release, without its leading `v`. "" when unreachable."""
    try:
        with urllib.request.urlopen(LATEST_RELEASE_API, timeout=API_TIMEOUT) as response:
            tag = json.load(response)["tag_name"]
    except (OSError, ValueError, KeyError):
        return ""
    return tag.removeprefix("v")


def _install_dir():
    """Folder holding the running release binary, or None when this is not one.

    PyApp replaces its own process with Python, so `sys.executable` is the embedded
    interpreter rather than the binary. `PYAPP_PASS_LOCATION` makes the launcher hand its own
    path over in `PYAPP` instead; binaries released before that option was set only carry the
    plain "1" flag, and for those the copy on PATH is the best guess available.
    """
    location = os.environ.get("PYAPP")
    if location is None:
        return None
    if location != "1":
        return Path(location).parent
    found = shutil.which("git-manager")
    return Path(found).parent if found else None


def upgrade(current):
    """Install the newest release over the running binary. Returns (ok, message)."""
    if sys.platform == "win32":
        return False, f"no self-upgrade on Windows — download the .exe from {RELEASES_PAGE}"

    bin_dir = _install_dir()
    if bin_dir is None:
        return False, "not a release binary — upgrade it the way you installed it"

    latest = latest_version()
    if not latest:
        return False, "could not reach the GitHub release API"
    if latest == current:
        return True, f"already on the latest version ({current})"

    # Output is left uncaptured so the installer's own progress reaches the terminal.
    # S603/S607: a fixed command, resolving `sh` from PATH the way install.sh itself is run.
    result = subprocess.run(  # noqa: S603
        ["sh", "-c", INSTALL_COMMAND],  # noqa: S607
        env={**os.environ, "BIN_DIR": str(bin_dir)},
        timeout=DOWNLOAD_TIMEOUT,
        check=False,
    )
    if result.returncode:
        return False, "the install script failed"
    return True, f"upgraded {current} to {latest}"
