"""Textual UI: a table of repositories plus a log pane. All git work happens in `git.py`."""

from pathlib import Path
from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Label, RichLog

from . import git as gitops

COLUMNS = ("", "repo", "branch", "default", "state", "behind", "ahead")

#: Marker drawn in the first column of a selected row.
MARK = "*"

DISCARD_WARNING = (
    "Discard ALL local changes in {repo}?\nreset --hard + clean -fd. Cannot be undone."
)

#: What each action key does: the git operation, and the label it logs per repository.
UPDATE = (gitops.update_default, "update default")
MERGE = (gitops.merge_default, "merge default -> current")
DISCARD = (gitops.discard, "discard")


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

    # Two layouts for the same two panes. Without `.side` the log sits under the table; with it
    # the log moves to the right, giving the repository list the full height of the screen.
    CSS = """
    #split { layout: vertical; }
    #split DataTable { width: 1fr; height: 1fr; }
    #split RichLog { width: 1fr; height: 12; border-top: solid $accent; }

    #split.side { layout: horizontal; }
    #split.side RichLog { width: 40; height: 1fr; border-top: none; border-left: solid $accent; }
    """
    BINDINGS: ClassVar[list] = [
        ("r", "refresh", "Rescan"),
        ("s", "split", "Split horizontal/vertical"),
        ("space", "select", "Select"),
        ("a", "select_all", "Select all"),
        ("i", "invert_selection", "Invert selection"),
        ("u", "update", "Update default"),
        ("U", "update_many", "Update selected/all"),
        ("m", "merge", "Merge default->current"),
        ("d", "discard", "Discard changes"),
        ("D", "discard_many", "Discard selected"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, root):
        super().__init__()
        self.root = Path(root).resolve()
        self.repos = []
        self.selected = set()

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="split"):
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
        """Replace the table contents. The only place `self.repos` is written."""
        self.repos = repos
        self.selected &= set(repos)
        t = self.query_one(DataTable)
        row = t.cursor_row
        t.clear()
        for repo, r in zip(repos, rows, strict=True):
            t.add_row(MARK if repo in self.selected else " ", *r)
        if rows:
            t.move_cursor(row=min(row, len(rows) - 1))
        self._write(f"[green]{len(rows)} repos[/]")

    def _current(self):
        """Repository under the cursor, or None when the table is empty."""
        if not self.repos:
            return None
        return self.repos[self.query_one(DataTable).cursor_row]

    def _marked(self):
        """Repositories marked with `space`, in table order."""
        return [r for r in self.repos if r in self.selected]

    def _remark(self):
        """Redraw the marker column from `self.selected`."""
        t = self.query_one(DataTable)
        for i, repo in enumerate(self.repos):
            t.update_cell_at((i, 0), MARK if repo in self.selected else " ")

    # --- worker-thread helpers -----------------------------------------
    def say(self, text):
        self.call_from_thread(self._write, text)

    def _rescan(self, repos):
        rows = [gitops.status(r, self.root) for r in repos]
        self.call_from_thread(self._fill, repos, rows)

    @work(thread=True)
    def _apply(self, repos, op, label) -> None:
        """Run `op` on each repository, log every result, then refresh the table once."""
        for repo in repos:
            self.say(f"[bold]{repo.name}[/] {label}")
            ok, msg = op(repo)
            self.say(msg if ok else f"[red]{msg}[/]")
        self._rescan(self.repos)

    # --- actions -------------------------------------------------------
    @work(thread=True, exclusive=True)
    def action_refresh(self) -> None:
        self.say(f"scanning {self.root} ...")
        self._rescan(gitops.find_repos(self.root))

    def action_split(self) -> None:
        """Move the log pane between under the table and beside it."""
        self.query_one("#split").toggle_class("side")

    def action_select(self) -> None:
        """Toggle the mark on the row under the cursor, then step down."""
        repo = self._current()
        if not repo:
            return
        self.selected ^= {repo}
        t = self.query_one(DataTable)
        t.update_cell_at((t.cursor_row, 0), MARK if repo in self.selected else " ")
        t.action_cursor_down()

    def action_select_all(self) -> None:
        self.selected = set(self.repos)
        self._remark()

    def action_invert_selection(self) -> None:
        self.selected = set(self.repos) - self.selected
        self._remark()

    def action_update(self) -> None:
        if repo := self._current():
            self._apply([repo], *UPDATE)

    def action_update_many(self) -> None:
        """Update every marked repository, or all of them when nothing is marked."""
        if repos := self._marked() or self.repos:
            self._apply(repos, *UPDATE)

    def action_merge(self) -> None:
        if repo := self._current():
            self._apply([repo], *MERGE)

    def action_discard(self) -> None:
        if repo := self._current():
            self._confirm_discard([repo], repo.name)

    def action_discard_many(self) -> None:
        """Discard in every marked repository. Marking is required — never a silent select-all."""
        repos = self._marked()
        if not repos:
            self._write("[yellow]nothing selected — mark rows with space[/]")
            return
        self._confirm_discard(repos, f"{len(repos)} selected repos")

    def _confirm_discard(self, repos, what):
        """Ask once for the whole set; discard only if the answer is yes."""
        self.push_screen(
            Confirm(DISCARD_WARNING.format(repo=what)),
            lambda ok: self._apply(repos, *DISCARD) if ok else None,
        )
