"""The Textual app, driven headlessly. Covers what the keys actually do to the repositories."""

import pytest
from textual.widgets import DataTable, RichLog

from conftest import commit, init_repo, sh
from git_manager import git as gm
from git_manager.ui import Confirm, GitManager


async def settle(app, pilot):
    """Wait for the thread workers a keypress started, then let the UI repaint."""
    await pilot.pause()
    await app.workers.wait_for_complete()
    await pilot.pause()


def rows_of(app):
    table = app.query_one(DataTable)
    return [tuple(table.get_row_at(i)) for i in range(table.row_count)]


@pytest.fixture
def app(tmp_path, upstream, clone):
    return GitManager(tmp_path)


async def test_startup_lists_every_repo(app, clone, upstream):
    async with app.run_test() as pilot:
        await settle(app, pilot)
        assert rows_of(app) == [
            ("a/b/repo", "main", "main", "-", "0", "0"),
            ("upstream", "main", "main", "-", "0", "0"),
        ]
        assert app.repos == [clone, upstream]


async def test_rescan_picks_up_a_new_repo(app, tmp_path):
    async with app.run_test() as pilot:
        await settle(app, pilot)
        before = len(app.repos)
        init_repo(tmp_path / "later")
        await pilot.press("r")
        await settle(app, pilot)
        assert len(app.repos) == before + 1


async def test_update_key_clears_behind(app, upstream, clone, tmp_path):
    commit(upstream, "theirs")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("u")
        await settle(app, pilot)
        assert gm.status(clone, tmp_path)[4] == "0"


async def test_merge_key_brings_the_default_in(app, upstream, clone):
    sh("git", "checkout", "-q", "-b", "feature", cwd=clone)
    commit(upstream, "theirs", "theirs.txt", "from the team\n")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("m")
        await settle(app, pilot)
        assert (clone / "theirs.txt").read_text() == "from the team\n"


async def test_discard_asks_first_and_escape_keeps_your_work(app, clone):
    (clone / "precious.txt").write_text("do not delete\n")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("d")
        await pilot.pause()
        assert isinstance(app.screen, Confirm)

        await pilot.press("escape")
        await settle(app, pilot)
        assert (clone / "precious.txt").read_text() == "do not delete\n"


async def test_discard_confirmed_throws_the_changes_away(app, clone):
    (clone / "junk.txt").write_text("x")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("d")
        await pilot.pause()
        await pilot.click("#yes")
        await settle(app, pilot)
        assert not (clone / "junk.txt").exists()


async def test_cancel_button_keeps_your_work(app, clone):
    (clone / "precious.txt").write_text("do not delete\n")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("d")
        await pilot.pause()
        await pilot.click("#no")
        await settle(app, pilot)
        assert (clone / "precious.txt").read_text() == "do not delete\n"


async def test_actions_do_nothing_when_there_is_no_repo(tmp_path):
    """An empty folder must not crash on a keypress."""
    empty = GitManager(tmp_path / "empty")
    (tmp_path / "empty").mkdir()
    async with empty.run_test() as pilot:
        await settle(empty, pilot)
        assert rows_of(empty) == []
        for key in ("u", "m", "d"):
            await pilot.press(key)
            await settle(empty, pilot)
        assert empty.repos == []


async def test_failures_are_reported_in_the_log(app, clone):
    sh("git", "remote", "set-url", "origin", "/nonexistent/repo.git", cwd=clone)
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("u")
        await settle(app, pilot)
        written = app.query_one(RichLog).lines
        assert written
