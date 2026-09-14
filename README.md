# git-manager

A terminal UI that scans a folder tree for git repositories and keeps them in sync with their
default branch (`main`/`master`). One screen, one keypress per action.

```
repo                  branch        default  state  behind  ahead
api                   feat/search   main     dirty  12      3
docs                  main          main     -      0       0
infra/terraform       master        master   -      4       0
```

## Install

Download a binary from the [latest release](../../releases), or run from source:

```sh
uv run git-manager            # scan the current folder
uv run git-manager ~/projects # scan another folder
```

`git` must be on your `PATH`. Everything else is bundled or resolved by `uv`.

Full options in [docs/installation.md](docs/installation.md).

## Keys

| Key | Action |
|-----|--------|
| `r` | Rescan the folder tree |
| `u` | Fetch, then update the default branch (fast-forward only) |
| `m` | Merge `origin/<default>` into the current branch |
| `d` | Discard local changes — asks for confirmation, cannot be undone |
| `q` | Quit |

Actions apply to the repository under the cursor. See [docs/usage.md](docs/usage.md) for what
each column means and how the scan decides what to list.

## Docs

| Page | For |
|------|-----|
| [Installation](docs/installation.md) | Getting it running on Linux, Windows or macOS |
| [Usage](docs/usage.md) | Keys, columns, scanning rules, safety |
| [Development](docs/development.md) | Layout, make targets, linting, tests |
| [Dependencies](docs/dependencies.md) | Where they live, how to add and upgrade them |
| [Releasing](docs/releasing.md) | Building binaries and cutting a release |
