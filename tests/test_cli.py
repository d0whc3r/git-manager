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
    main()
    assert "usage: git-manager [folder]" in capsys.readouterr().out
    assert launched == {}


@pytest.mark.parametrize("flag", ["-V", "--version"])
def test_version_prints_the_version_and_starts_nothing(flag, monkeypatch, capsys, launched):
    monkeypatch.setattr(sys, "argv", ["git-manager", flag])
    main()
    assert capsys.readouterr().out.strip() == f"git-manager {__version__}"
    assert launched == {}


def test_no_argument_scans_the_current_folder(monkeypatch, launched):
    monkeypatch.setattr(sys, "argv", ["git-manager"])
    main()
    assert launched == {"root": ".", "ran": True}


def test_an_argument_is_used_as_the_scan_root(monkeypatch, launched):
    monkeypatch.setattr(sys, "argv", ["git-manager", "/projects/elsewhere"])
    main()
    assert launched == {"root": "/projects/elsewhere", "ran": True}
