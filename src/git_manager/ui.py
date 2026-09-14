"""Textual UI: a table of repositories plus a log pane. All git work happens in `git.py`."""

from pathlib import Path
from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Label, RichLog

from . import git as gitops

COLUMNS = ("repo", "branch", "default", "state", "behind", "ahead")

DISCARD_WARNING = (
    "Discard ALL local changes in {repo}?\nreset --hard + clean -fd. Cannot be undone."
)


class Confirm(ModalScreen[bool]):
    """Yes/no dialog. Dismisses with True only when the destructive button is pressed."""

    CSS = """
    Confirm { align: center middle; }
    #dialog { width: 60; height: auto; border: thick $error; background: $surface; padding: 1 2; }
    """
    BINDINGS: ClassVar[list] = [("escape", "dismiss(False)", "Cancel")]

    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.msg)
            yield Button("Cancel", variant="primary", id="no")
            yield Button("Yes, discard", variant="error", id="yes")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


class GitManager(App):
    TITLE = "git-manager"
    CSS = "DataTable { height: 1fr; } RichLog { height: 12; border-top: solid $accent; }"
    BINDINGS: ClassVar[list] = [
        ("r", "refresh", "Rescan"),
        ("u", "update", "Update default"),
        ("m", "merge", "Merge default->current"),
        ("d", "discard", "Discard changes"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, root):
        super().__init__()
        self.root = Path(root).resolve()
        self.repos = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(cursor_type="row")
        yield RichLog(markup=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(DataTable).add_columns(*COLUMNS)
        self.action_refresh()

    # --- main-thread helpers -------------------------------------------
    def _write(self, text):
        self.query_one(RichLog).write(text)

    def _fill(self, repos, rows):
        self.repos = repos
        t = self.query_one(DataTable)
        row = t.cursor_row
        t.clear()
        for r in rows:
            t.add_row(*r)
        if rows:
            t.move_cursor(row=min(row, len(rows) - 1))
        self._write(f"[green]{len(rows)} repos[/]")

    def _current(self):
        """Repository under the cursor, or None when the table is empty."""
        if not self.repos:
            return None
        return self.repos[self.query_one(DataTable).cursor_row]

    # --- worker-thread helpers -----------------------------------------
    def say(self, text):
        self.call_from_thread(self._write, text)

    def _rescan(self):
        rows = [gitops.status(r, self.root) for r in self.repos]
        self.call_from_thread(self._fill, self.repos, rows)

    def _run(self, repo, op, label):
        self.say(f"[bold]{repo.name}[/] {label}")
        ok, msg = op(repo)
        self.say(msg if ok else f"[red]{msg}[/]")
        self._rescan()

    # --- actions -------------------------------------------------------
    @work(thread=True, exclusive=True)
    def action_refresh(self) -> None:
        self.say(f"scanning {self.root} ...")
        self.repos = gitops.find_repos(self.root)
        self._rescan()

    def action_update(self) -> None:
        repo = self._current()
        if repo:
            self._update(repo)

    @work(thread=True)
    def _update(self, repo) -> None:
        self._run(repo, gitops.update_default, "update default")

    def action_merge(self) -> None:
        repo = self._current()
        if repo:
            self._merge(repo)

    @work(thread=True)
    def _merge(self, repo) -> None:
        self._run(repo, gitops.merge_default, "merge default -> current")

    def action_discard(self) -> None:
        repo = self._current()
        if not repo:
            return
        self.push_screen(
            Confirm(DISCARD_WARNING.format(repo=repo.name)),
            lambda ok: self._discard(repo) if ok else None,
        )

    @work(thread=True)
    def _discard(self, repo) -> None:
        self._run(repo, gitops.discard, "discard")
