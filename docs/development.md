# Development

```sh
make help    # list every target
```

| Target | What it does |
|--------|--------------|
| `sync` | Create `.venv` and install dependencies from `uv.lock` |
| `run` | Run the TUI (`DIR=<path>` to scan another folder) |
| `lint` | Check lint rules and formatting, changing nothing |
| `fmt` | Apply lint fixes and format the code |
| `test` | Run the test suite with coverage |
| `cov` | Write an HTML coverage report to `htmlcov/` |
| `build` | Build a standalone binary into `dist/` |
| `install` | Install `git-manager` on your `PATH` |
| `uninstall` | Remove it from your `PATH` |
| `upgrade` | Upgrade locked dependencies to their latest allowed versions |
| `clean` | Remove build artifacts |

On Windows there is no `make` by default — run the commands from the `Makefile` directly.

## Layout

```
src/git_manager/
  git.py        # domain: shells out to git, returns plain data. No UI, no state.
  ui.py         # Textual app and modal. No subprocess calls.
  __main__.py   # argument handling and entry point
tests/
  conftest.py   # fixtures: throwaway repositories, isolated git config
  test_*.py     # one file per concern, see Tests below
```

The split is the point. `git.py` is importable and testable without a terminal, and `ui.py`
never calls `subprocess` itself.

Every mutating operation — `update_default`, `merge_default`, `discard` — lives in `git.py` and
returns `(ok, message)`. The UI just renders the message, which is why all three actions share
one `_run(repo, op, label)` worker.

Adding an action means writing one function in `git.py` that returns `(ok, message)`, then a
binding and a two-line worker in `ui.py`.

## Threads

Git calls block, so every action runs on a Textual thread worker (`@work(thread=True)`).
Anything touching widgets from a worker goes through `call_from_thread`. The helpers make the
rule visible: `_write` and `_fill` run on the main thread, `say` and `_rescan` are the
worker-side wrappers.

Reading the cursor position happens in the action method, on the main thread, before the worker
starts — never inside it.

## Linting and formatting

Both are [ruff](https://docs.astral.sh/ruff/):

```sh
make lint   # reports, changes nothing
make fmt    # rewrites
```

CI runs both checks and fails on any difference, so run `make fmt` before pushing.

Rules live under `[tool.ruff.lint]` in `pyproject.toml`, each line commented with what it buys.
The ones worth knowing about:

| Set | Catches |
|-----|---------|
| `B` | Mutable default arguments, loop-variable capture, and similar real bugs |
| `S` | Security footguns — `subprocess` misuse, `assert` in shipped code, hardcoded secrets |
| `SIM`, `RET`, `PERF`, `FURB` | Code that can be shorter, flatter, or faster |
| `PTH` | `os.path` calls that should be `pathlib` |
| `T20` | Stray `print()` left behind from debugging |
| `SLF` | Reaching into another object's private members |
| `C90` | Functions over complexity 10 |
| `PGH` | Blanket `# noqa` with no rule code |

`PGH` is the one that keeps the rest honest: every suppression has to name the rule it silences,
so nothing gets muted by accident. There are three in the codebase, all in `git.py`, all with a
comment above them explaining why shelling out to `git` from `PATH` is the intended design.

Deliberately not enabled: `ANN` (type annotations) and `D` (docstrings on every public symbol).
Together they flag 60-odd sites in a 300-line project, most of them Textual lifecycle methods
whose signatures the framework already defines. Turn them on if the project grows enough to
need them.

Per-file exceptions live under `[tool.ruff.lint.per-file-ignores]`: the self-check may use
`assert`, shell out to `git`, and `print`; `__main__.py` may `print`.

## Tests

```sh
make test   # pytest with coverage, fails under 95%
make cov    # same, plus an HTML report in htmlcov/
```

47 tests, 99% coverage. They run against throwaway repositories built under pytest's `tmp_path`
and touch nothing else.

| File | Covers |
|------|--------|
| `tests/conftest.py` | Fixtures: an `upstream` repo and a `clone` of it, nested two folders deep |
| `tests/test_discovery.py` | `find_repos` and the branch-name lookups |
| `tests/test_status.py` | The six columns, including the cases that render `-` and `?` |
| `tests/test_operations.py` | `update_default`, `merge_default`, `discard` |
| `tests/test_ui.py` | The app driven headlessly through `App.run_test()` |
| `tests/test_cli.py` | `--help`, `--version`, and which folder gets scanned |

### Git is isolated from your machine

A session fixture points `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` at a file that does not
exist, and sets the author and committer identity from the environment. Your own `.gitconfig` —
default branch name, commit signing, aliases, hooks — cannot change the result, so the suite
behaves the same on your laptop and in CI.

### Testing the UI

`tests/test_ui.py` drives the real app with Textual's `App.run_test()`, so the assertions are
about what a keypress does to the repositories on disk, not about which method got called.

Every action runs on a thread worker, so each test waits with a `settle()` helper —
`pilot.pause()`, then `app.workers.wait_for_complete()`, then `pilot.pause()` again — before
asserting. Without it you are racing the worker and the test is flaky.

Both branches of the destructive path are covered: `Escape` and the Cancel button must leave an
uncommitted file untouched, and only the confirm button may delete it.

### What is not covered

One branch in `status()`: `git rev-list` exiting 0 but printing something other than two
numbers. Reaching it means faking git's output, which would test the mock rather than the code.

Anything that needs the network. The tests clone over the filesystem, so `fetch` and `merge` are
exercised, but no remote is ever contacted.
