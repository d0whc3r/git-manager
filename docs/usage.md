# Usage

The screen is a table of repositories over a log pane. Move with the arrow keys; lowercase
actions apply to the repository under the cursor, uppercase ones to a whole set.

## Keys

| Key | Action |
|-----|--------|
| `r` | Rescan the folder tree |
| `s` | Move the log pane between under the table and beside it |
| `space` | Mark or unmark the repository under the cursor, then step down |
| `a` | Mark every repository |
| `i` | Invert the marks: unmarked rows become marked, marked ones become unmarked |
| `u` | Fetch, then update the default branch (fast-forward only) |
| `U` | Same, for every marked repository — or all of them when none are marked |
| `m` | Merge `origin/<default>` into the current branch |
| `d` | Discard local changes (`reset --hard` + `clean -fd`) — asks for confirmation |
| `D` | Same, for every marked repository — one confirmation for the whole set |
| `q` | Quit |

### `s` — split the screen the other way

By default the log pane sits under the table and takes 12 rows. `s` moves it to the right of
the table instead, 40 columns wide, which gives the repository list the full height of the
screen — worth it once the list is longer than fits.

### `space`, `a`, `i` — mark repositories for a batch action

Marked rows carry a `*` in the first column. `U` and `D` then work through the marked set in
table order, logging each repository as it goes, and refresh the table once at the end.

`a` marks every repository at once, `i` flips every mark — so `a` then `i` clears the set.

### `u` — update the default branch

Runs `git fetch --all --prune`, then brings the local default branch up to date. If you have
the default branch checked out it fast-forwards it; otherwise it updates the branch ref without
touching your working tree, so you can stay on your feature branch.

Fast-forward only. If the default branch has diverged locally, the log says so and nothing is
rewritten.

### `m` — merge the default branch into yours

Fetches, then merges `origin/<default>` into the branch you have checked out. This is how you
bring your branch up to date with the rest of the team.

Conflicts are left in place for you to resolve with your normal tools — git-manager does not
try to resolve them.

### `d` — discard local changes

> **Warning:** this permanently deletes every uncommitted change and every untracked file in
> that repository. There is no undo. A confirmation dialog appears first; `Esc` cancels it.

Runs `git reset --hard` followed by `git clean -fd`.

`D` does the same across every marked repository. Unlike `U`, it never falls back to "all":
with nothing marked it refuses and says so in the log, so a stray keypress cannot wipe the
whole tree.

## Columns

| Column | Meaning |
|--------|---------|
| `repo` | Path relative to the scanned root |
| `branch` | Currently checked-out branch |
| `default` | Default branch, from `origin/HEAD`, falling back to `main` then `master` |
| `state` | `dirty` if the working tree has changes, `-` otherwise |
| `behind` | Commits on the default branch that your branch lacks |
| `ahead` | Commits on your branch that the default branch lacks |

`behind` and `ahead` compare against `origin/<default>` when that remote-tracking ref exists,
and against the local default branch otherwise. They are only as fresh as your last fetch —
press `u` to refresh them against the remote.

A `-` in `behind` or `ahead` means the comparison could not be made, usually because no default
branch was found.

## What gets scanned

- Up to 6 levels deep from the folder you start in.
- Descent continues past a repository, so submodules and nested checkouts get their own row.
- These are skipped: `node_modules`, `venv`, `.venv`, `target`, `vendor`, `Library`, and any
  folder starting with a dot.
- Symlinks are not followed.

To change the depth or the skip list, edit `MAX_DEPTH` and `SKIP` at the top of
`src/git_manager/git.py`.
