"""The command line entry point: flags, and which folder gets scanned."""

import sys

import pytest

from git_manager import __version__
from git_manager.__main__ import main


@pytest.fixture
def launched(monkeypatch):
    """Replace the app so `main` can be exercised without starting a terminal UI."""
    seen = {}

    class FakeApp:
        def __init__(self, root):
            seen["root"] = root

        def run(self):
            seen["ran"] = True

    monkeypatch.setattr("git_manager.ui.GitManager", FakeApp)
    return seen


@pytest.mark.parametrize("flag", ["-h", "--help"])
def test_help_prints_usage_and_starts_nothing(flag, monkeypatch, capsys, launched):
    monkeypatch.setattr(sys, "argv", ["git-manager", flag])
    assert main() == 0
    assert "usage: git-manager [folder]" in capsys.readouterr().out
    assert launched == {}


@pytest.mark.parametrize("flag", ["-V", "--version"])
def test_version_prints_the_version_and_starts_nothing(flag, monkeypatch, capsys, launched):
    monkeypatch.setattr(sys, "argv", ["git-manager", flag])
    assert main() == 0
    assert capsys.readouterr().out.strip() == f"git-manager {__version__}"
    assert launched == {}


def test_no_argument_scans_the_current_folder(monkeypatch, launched):
    monkeypatch.setattr(sys, "argv", ["git-manager"])
    assert main() == 0
    assert launched == {"root": ".", "ran": True}


def test_an_argument_is_used_as_the_scan_root(tmp_path, monkeypatch, launched):
    monkeypatch.setattr(sys, "argv", ["git-manager", str(tmp_path)])
    assert main() == 0
    assert launched == {"root": str(tmp_path), "ran": True}


def test_a_folder_that_does_not_exist_exits_with_an_error(monkeypatch, capsys, launched):
    """A typo must say so, not open an empty table."""
    monkeypatch.setattr(sys, "argv", ["git-manager", "/no/such/folder"])
    assert main() == 1
    assert "not a folder: /no/such/folder" in capsys.readouterr().err
    assert launched == {}


def test_an_unknown_flag_is_rejected(monkeypatch, capsys, launched):
    monkeypatch.setattr(sys, "argv", ["git-manager", "--nope"])
    assert main() == 1
    assert "not a folder" in capsys.readouterr().err
    assert launched == {}
