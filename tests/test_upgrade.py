"""Self-upgrade: which file gets replaced, and when the download is skipped."""

import io
import json
import subprocess
import sys

import pytest

from git_manager import upgrade as up


@pytest.fixture
def release(monkeypatch):
    """Pretend the newest published release is 9.9.9, and record the installer invocation."""
    monkeypatch.setattr(up, "latest_version", lambda: "9.9.9")
    ran = {}

    def fake_run(cmd, env, timeout, check):
        ran.update(cmd=cmd, bin_dir=env["BIN_DIR"], timeout=timeout, check=check)
        return subprocess.CompletedProcess(cmd, ran.get("rc", 0))

    monkeypatch.setattr(up.subprocess, "run", fake_run)
    monkeypatch.setattr(sys, "platform", "linux")
    return ran


def test_the_launcher_path_decides_where_the_new_binary_lands(monkeypatch, release):
    """PYAPP_PASS_LOCATION puts the running binary's path in $PYAPP."""
    monkeypatch.setenv("PYAPP", "/opt/tools/git-manager")
    assert up.upgrade("0.1.0") == (True, "upgraded 0.1.0 to 9.9.9")
    assert release["bin_dir"] == "/opt/tools"


def test_an_older_binary_falls_back_to_the_copy_on_path(monkeypatch, release):
    """Binaries built before PYAPP_PASS_LOCATION only set the flag."""
    monkeypatch.setenv("PYAPP", "1")
    monkeypatch.setattr(up.shutil, "which", lambda _: "/home/u/.local/bin/git-manager")
    assert up.upgrade("0.1.0")[0] is True
    assert release["bin_dir"] == "/home/u/.local/bin"


def test_an_older_binary_that_is_not_on_path_is_refused(monkeypatch, release):
    monkeypatch.setenv("PYAPP", "1")
    monkeypatch.setattr(up.shutil, "which", lambda _: None)
    ok, msg = up.upgrade("0.1.0")
    assert (ok, "release binary" in msg) == (False, True)
    assert release == {}


def test_running_from_source_is_refused(monkeypatch, release):
    """Without $PYAPP there is no binary to replace — uv owns that install."""
    monkeypatch.delenv("PYAPP", raising=False)
    ok, msg = up.upgrade("0.1.0")
    assert (ok, "release binary" in msg) == (False, True)
    assert release == {}


def test_the_current_version_skips_the_download(monkeypatch, release):
    monkeypatch.setenv("PYAPP", "/opt/tools/git-manager")
    assert up.upgrade("9.9.9") == (True, "already on the latest version (9.9.9)")
    assert release == {}


def test_an_unreachable_api_reports_instead_of_downloading(monkeypatch, release):
    monkeypatch.setenv("PYAPP", "/opt/tools/git-manager")
    monkeypatch.setattr(up, "latest_version", lambda: "")
    assert up.upgrade("0.1.0") == (False, "could not reach the GitHub release API")
    assert release == {}


def test_a_failing_install_script_is_reported(monkeypatch, release):
    monkeypatch.setenv("PYAPP", "/opt/tools/git-manager")
    release["rc"] = 1
    assert up.upgrade("0.1.0") == (False, "the install script failed")


def test_windows_is_pointed_at_the_release_page(monkeypatch, release):
    """install.sh has no Windows path, so neither does this."""
    monkeypatch.setenv("PYAPP", r"C:\tools\git-manager.exe")
    monkeypatch.setattr(sys, "platform", "win32")
    ok, msg = up.upgrade("0.1.0")
    assert (ok, up.RELEASES_PAGE in msg) == (False, True)
    assert release == {}


def test_latest_version_drops_the_tag_prefix(monkeypatch):
    monkeypatch.setattr(
        up.urllib.request,
        "urlopen",
        lambda *_a, **_k: io.BytesIO(json.dumps({"tag_name": "v1.2.3"}).encode()),
    )
    assert up.latest_version() == "1.2.3"


@pytest.mark.parametrize(
    "response",
    [OSError("no network"), io.BytesIO(b"not json"), io.BytesIO(b"{}")],
    ids=["unreachable", "malformed", "no tag"],
)
def test_latest_version_is_empty_when_the_api_does_not_answer(monkeypatch, response):
    def urlopen(*_a, **_k):
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(up.urllib.request, "urlopen", urlopen)
    assert up.latest_version() == ""
