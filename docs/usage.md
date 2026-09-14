# Usage

The screen is a table of repositories over a log pane. Move with the arrow keys; every action
applies to the repository under the cursor.

## Keys

| Key | Action |
|-----|--------|
| `r` | Rescan the folder tree |
| `u` | Fetch, then update the default branch (fast-forward only) |
| `m` | Merge `origin/<default>` into the current branch |
| `d` | Discard local changes (`reset --hard` + `clean -fd`) — asks for confirmation |
| `q` | Quit |

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

- Up to 3 levels deep from the folder you start in.
- Descent stops at the first repository found, so submodules are not listed separately.
- These are skipped: `node_modules`, `venv`, `.venv`, `target`, `vendor`, `Library`, and any
  folder starting with a dot.
- Symlinks are not followed.

To change the depth or the skip list, edit `MAX_DEPTH` and `SKIP` at the top of
`src/git_manager/git.py`.
