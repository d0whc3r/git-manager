# git-manager

A terminal UI that scans a folder tree for git repositories and keeps them in sync with their
default branch (`main`/`master`). One screen, one keypress per action.

```
  repo                  branch        default  state  behind  ahead
* api                   feat/search   main     dirty  12      3
  docs                  main          main     -      0       0
* infra/terraform       master        master   -      4       0
```

## Install

A binary, no Python needed — Linux and macOS:

```sh
curl -fsSL https://raw.githubusercontent.com/d0whc3r/git-manager/main/install.sh | sh
```

Or with [uv](https://docs.astral.sh/uv/), which also covers Windows:

```sh
uv tool install git+https://github.com/d0whc3r/git-manager
```

Windows without `uv`: download the `.exe` from the [latest release](../../releases).

```sh
git-manager            # scan the current folder
git-manager ~/projects # scan another folder
```

`git` must be on your `PATH`. Everything else is bundled.

Full options in [docs/installation.md](docs/installation.md).

## Keys

| Key | Action |
|-----|--------|
| `r` | Rescan the folder tree |
| `s` | Move the log pane between under the table and beside it |
| `space` | Mark or unmark the repository under the cursor |
| `a` | Mark every repository |
| `i` | Invert the marks |
| `u` | Fetch, then update the default branch (fast-forward only) |
| `U` | Update every marked repository — or all of them when none are marked |
| `m` | Merge `origin/<default>` into the current branch |
| `d` | Discard local changes — asks for confirmation, cannot be undone |
| `D` | Discard in every marked repository — one confirmation, cannot be undone |
| `c` | Discard local changes, then check out the default branch — cannot be undone |
| `C` | Same, for every marked repository — one confirmation, cannot be undone |
| `q` | Quit |

Lowercase keys act on the repository under the cursor, uppercase ones on the marked set. See [docs/usage.md](docs/usage.md) for what
each column means and how the scan decides what to list.

## Docs

| Page | For |
|------|-----|
| [Installation](docs/installation.md) | Getting it running on Linux, Windows or macOS |
| [Usage](docs/usage.md) | Keys, columns, scanning rules, safety |
| [Development](docs/development.md) | Layout, make targets, linting, tests |
| [Dependencies](docs/dependencies.md) | Where they live, how to add and upgrade them |
| [Releasing](docs/releasing.md) | Building binaries and cutting a release |
