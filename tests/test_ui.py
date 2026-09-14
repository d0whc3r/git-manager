"""The Textual app, driven headlessly. Covers what the keys actually do to the repositories."""

import shutil

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
    """Table rows without the selection marker."""
    table = app.query_one(DataTable)
    return [tuple(table.get_row_at(i))[1:] for i in range(table.row_count)]


def marks_of(app):
    """The selection marker of every row, in table order."""
    table = app.query_one(DataTable)
    return [table.get_row_at(i)[0] for i in range(table.row_count)]


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
        for key in ("space", "u", "U", "m", "d", "D", "s"):
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


async def test_space_marks_the_row_and_moves_on(app):
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("space")
        await pilot.pause()
        assert marks_of(app) == ["*", " "]
        assert app.query_one(DataTable).cursor_row == 1

        await pilot.press("up", "space")
        await pilot.pause()
        assert marks_of(app) == [" ", " "]


async def test_update_all_key_updates_every_repo(app, upstream, clone, tmp_path):
    """`U` with nothing marked touches all of them, not only the row under the cursor."""
    commit(upstream, "theirs")
    second = init_repo(tmp_path / "second")
    sh("git", "clone", "-q", str(second), str(tmp_path / "second-clone"), cwd=tmp_path)
    commit(second, "more")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("U")
        await settle(app, pilot)
        assert gm.status(clone, tmp_path)[4] == "0"
        assert gm.status(tmp_path / "second-clone", tmp_path)[4] == "0"


async def test_discard_selected_spares_the_unmarked_repos(app, clone, upstream):
    (clone / "junk.txt").write_text("x")
    (upstream / "precious.txt").write_text("do not delete\n")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("space")  # marks the clone, cursor moves to upstream
        await pilot.press("D")
        await pilot.pause()
        await pilot.click("#yes")
        await settle(app, pilot)
        assert not (clone / "junk.txt").exists()
        assert (upstream / "precious.txt").read_text() == "do not delete\n"


async def test_discard_selected_does_nothing_without_a_mark(app, clone):
    """No mark must never mean "every repository" for a destructive action."""
    (clone / "precious.txt").write_text("do not delete\n")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        await pilot.press("D")
        await settle(app, pilot)
        assert not isinstance(app.screen, Confirm)
        assert (clone / "precious.txt").read_text() == "do not delete\n"


async def test_split_key_moves_the_log_beside_the_table(app):
    async with app.run_test() as pilot:
        await settle(app, pilot)
        split = app.query_one("#split")
        under = app.query_one(RichLog).size

        await pilot.press("s")
        await pilot.pause()
        assert split.has_class("side")
        beside = app.query_one(RichLog).size
        assert beside.height > under.height
        assert beside.width < under.width

        await pilot.press("s")
        await pilot.pause()
        assert not split.has_class("side")
        assert app.query_one(RichLog).size == under


async def test_rescan_forgets_marks_for_repos_that_are_gone(app, tmp_path, upstream):
    """A mark must not outlive the repository it pointed at."""
    gone = init_repo(tmp_path / "temporary")
    async with app.run_test() as pilot:
        await settle(app, pilot)
        app.query_one(DataTable).move_cursor(row=app.repos.index(gone))
        await pilot.press("space")
        await pilot.pause()
        assert app.selected == {gone}

        shutil.rmtree(gone)
        await pilot.press("r")
        await settle(app, pilot)
        assert app.selected == set()
